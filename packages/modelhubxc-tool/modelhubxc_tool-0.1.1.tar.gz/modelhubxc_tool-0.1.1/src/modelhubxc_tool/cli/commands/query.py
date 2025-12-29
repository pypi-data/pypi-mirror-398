import typer
import requests
from rich import print as rprint
from rich.table import Table
from modelhubxc_tool.utils import format_datetime



def query(model_id: str = typer.Argument(..., help="Model ID in format owner/model-name")):
    """
    Query model information by model ID
    """
    if "/" not in model_id:
        typer.echo(f"错误: 无效的模型 ID 格式 '{model_id}'。期望格式: owner/model-name (例如: zpm/Llama-3.1-PersianQA)")
        raise typer.Exit(1)
    
    api_url = f"https://modelhub.org.cn//api/computility/models/search-by-model-id?modelId={model_id}"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            model_data = data["data"]
            
            if not model_data.get("isInDB", False):
                typer.echo(f"模型：{model_id} 尚未录入")
                return
            
            table = Table(title=f"模型信息: {model_id}")
            table.add_column("字段", style="cyan")
            table.add_column("值", style="magenta")
            
            model_info = model_data.get("modelInfo", {})
            table.add_row("modelId", model_info.get("modelId", ""))
            table.add_row("创建时间", format_datetime(model_info.get("createTime", "")))
            table.add_row("作者", model_info.get("authorName", ""))
            table.add_row("来源", model_info.get("source", ""))
            
            rprint(table)
            
            verify_result = model_data.get("verifyResult")
            if not verify_result or len(verify_result) == 0:
                typer.echo(f"该模型尚未做验证")
            else:
                verify_table = Table(title="验证情况")
                verify_table.add_column("GPU类型", style="cyan")
                verify_table.add_column("GPU验证结果", style="orange3")
                verify_table.add_column("时间", style="green")
                verify_table.add_column("验证人", style="blue")
                verify_table.add_column("首次验证", style="magenta")
                verify_table.add_column("单次验证结果", style="red")
                
                for gpu_type, gpu_info in verify_result.items():
                    gpu_result = gpu_info.get("result", "")
                    records = gpu_info.get("records", [])
                    if records:
                        for idx, record in enumerate(records):
                            create_time = format_datetime(record.get("createTime", ""))
                            author_name = record.get("authorName", "")
                            is_new_model = "是" if record.get("isNewModel", False) else "否"
                            
                            verify_status = record.get("verifyResult", None)
                            if verify_status == 1:
                                verify_status_text = "验证成功"
                            elif verify_status == -1:
                                verify_status_text = "验证失败"
                            elif verify_status == 0:
                                verify_status_text = "待验证"
                            else:
                                verify_status_text = str(verify_status)
                            
                            if idx == 0:
                                verify_table.add_row(gpu_type, gpu_result, create_time, author_name, is_new_model, verify_status_text)
                            else:
                                verify_table.add_row("", "", create_time, author_name, is_new_model, verify_status_text)
                    else:
                        verify_table.add_row(gpu_type, gpu_result, "", "", "", "")
                
                rprint(verify_table)
        else:
            typer.echo(f"未找到模型: {model_id}")
            
    except requests.exceptions.RequestException as e:
        typer.echo(f"请求失败: {e}")
        raise typer.Exit(1)
