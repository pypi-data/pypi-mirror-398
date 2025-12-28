import yaml
from fastapi import APIRouter, Query, Response

from core.clash import ClashYamlGenerator, get_generator_dependency

router = APIRouter()


@router.get(
    "/sub",
    summary="转换订阅(可以转换多个订阅)",
    description="根据提供的URL、User-Agent和名称获取并处理订阅信息,返回YAML格式的Clash配置",
    response_description="返回YAML格式的Clash配置文件",
)
async def sub(
    urls: str = Query(..., description="订阅URL,逗号分隔"),
    agents: str = Query(
        "clash-verge/v2.4.3",
        description="User-Agent,逗号分隔(根据客户段选择)",
    ),
    names: str = Query(
        "订阅1", description="订阅名称,逗号分隔(可选,在客户端中的显示名)"
    ),
    generator: ClashYamlGenerator = get_generator_dependency(),
):
    # 将JSON字符串解析为Python对象
    sub_list = generator.query2sub(urls, agents, names)
    yaml_content, userinfo = generator.gen(sub_list)
    yaml_string = yaml.dump(yaml_content, allow_unicode=True, default_flow_style=False)
    return Response(
        headers={"Subscription-Userinfo": userinfo},
        content=yaml_string,
        media_type="text/yaml",
    )
