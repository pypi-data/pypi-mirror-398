import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style

# 路由配置参数
from configs import RouterConfig, LayoutConfig


def render():
    """渲染核心功能页面侧边菜单栏"""

    return fac.AntdAffix(
        fuc.FefferyDiv(
            [
                # 侧边菜单
                fac.AntdMenu(
                    id="core-side-menu",
                    menuItems=RouterConfig.core_side_menu,
                    mode="inline",
                    style=style(border="none", width="100%"),
                )
            ],
            scrollbar="hidden",
            style=style(
                height="calc(100vh - 72px)",
                overflowY="auto",
                borderRight="1px solid #dae0ea",
                padding="0 8px",
            ),
        ),
        id="core-side-menu-affix",
        offsetTop=72.1,
        style=style(width=LayoutConfig.core_side_width),
    )
