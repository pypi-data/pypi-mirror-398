from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html, swagger_ui_default_parameters


def custom_swagger_ui_html(*args, **kwargs):
    custom_params = {
        "dom_id": "#swagger-ui",
        "layout": "BaseLayout",
        "deepLinking": True,
        "showExtensions": True,
        "showCommonExtensionsExtensions": True,
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
        "displayRequestDuration": True
    }

    # 初始化合并参数为默认参数的副本
    merged_params = swagger_ui_default_parameters.copy()

    # 安全地合并kwargs中的参数（处理可能为None的情况）
    if "swagger_ui_parameters" in kwargs and kwargs["swagger_ui_parameters"] is not None:
        merged_params.update(kwargs["swagger_ui_parameters"])

    # 最后应用自定义参数
    merged_params.update(custom_params)
    kwargs["swagger_ui_parameters"] = merged_params

    return get_swagger_ui_html(
        *args, ** kwargs,
        swagger_favicon_url="https://static.sytechnology.com/img/sylogopng.png",
        swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui.css",
    )


def custom_redoc_html(*args, **kwargs):
    return get_redoc_html(
        *args,
        **kwargs,
        redoc_favicon_url='https://static.sytechnology.com/img/sylogopng.png',
        # redoc_js_url="https://cdn.jsdelivr.net/npm/@stardustai/redoc@2.0.0-rc.66/bundles/redoc.browser.lib.min.js",
        with_google_fonts=False,
    )
