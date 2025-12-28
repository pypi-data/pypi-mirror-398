from fastapi.middleware.cors import CORSMiddleware


def setup_cors_handler(app):
    # 允许所有源访问（*）
    # 注意：此时allow_credentials必须为False，否则浏览器会拦截响应
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=["*"],         # 允许所有源
        # allow_credentials=False,     # 必须为False（与*配合）
        # allow_methods=["*"],         # 允许所有HTTP方法
        allow_headers=["*"],         # 允许所有请求头
        expose_headers=["*"]         # 允许前端访问所有响应头
    )

    return app
