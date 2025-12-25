from typing import Dict, Any, Optional, List, Union

from sycommon.synacos.param import Body, Cookie, File, Form, Header, Path, Query
from sycommon.synacos.feign_client import feign_client, feign_request, feign_upload


@feign_client(
    service_name="product-service",
    path_prefix="/api/v1",
    default_headers={
        "User-Agent": "Feign-Client/1.0",
        "Accept": "application/json"
    }
)
class ProductServiceClient:
    """商品服务Feign客户端（优化版）"""

    # ------------------------------
    # 场景1: 基础参数 + 动态Header + Cookie
    # ------------------------------
    @feign_request(
        "GET",
        "/products/{product_id}/reviews",
        headers={"X-Request-Source": "mobile"},  # 固定头
        timeout=10  # 接口级超时（10秒）
    )
    async def get_product_reviews(
        self,
        product_id: int = Path(..., description="商品ID"),
        status: Optional[str] = Query(None, description="评价状态"),
        page: int = Query(1, description="页码"),
        size: int = Query(10, description="每页条数"),
        x_auth_token: str = Header(..., description="动态令牌头"),  # 动态头
        session_id: str = Cookie(..., description="会话Cookie")  # Cookie
    ) -> Dict[str, Any]:
        """获取商品评价列表"""
        pass

    # ------------------------------
    # 场景2: 仅Query参数（默认不超时）
    # ------------------------------
    @feign_request("GET", "/products")  # 未指定timeout，使用客户端默认（不超时）
    async def search_products(
        self,
        category: str = Query(..., description="商品分类"),
        min_price: Optional[float] = Query(None, description="最低价格"),
        max_price: Optional[float] = Query(None, description="最高价格"),
        sort: str = Query("created_desc", description="排序方式")
    ) -> Dict[str, Any]:
        """搜索商品"""
        pass

    # ------------------------------
    # 场景3: JSON请求体 + 动态签名头
    # （通过Header参数传递动态生成的签名）
    # ------------------------------
    @feign_request(
        "POST",
        "/products",
        headers={"s-y-version": "2.1"},
        timeout=15  # 15秒超时
    )
    async def create_product(
        self,
        product_data: Dict[str, Any] = Body(..., description="商品信息"),
        x_signature: str = Header(..., description="动态生成的签名头")  # 签名头
    ) -> Dict[str, Any]:
        """创建商品（动态签名通过Header参数传递）"""
        pass

    # ------------------------------
    # 场景4: 文件上传 + 分片上传头
    # ------------------------------
    @feign_upload(field_name="image_file")
    @feign_request(
        "POST",
        "/products/{product_id}/images",
        headers={"X-Upload-Type": "product-image"},
        timeout=60  # 上传超时60秒
    )
    async def upload_product_image(
        self,
        product_id: int = Path(..., description="商品ID"),
        file_paths: Union[str, List[str]] = File(..., description="文件路径"),
        image_type: str = Form(..., description="图片类型"),
        is_primary: bool = Form(False, description="是否主图"),
        x_chunked: bool = Header(False, description="是否分片上传")  # 分片上传头
    ) -> Dict[str, Any]:
        """上传商品图片（支持分片上传标记）"""
        pass

    # ------------------------------
    # 场景5: 表单提交 + 操作时间头
    # ------------------------------
    @feign_request(
        "POST",
        "/products/batch-status",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    async def batch_update_status(
        self,
        product_ids: str = Form(..., description="商品ID列表"),
        status: str = Form(..., description="目标状态"),
        operator: str = Form(..., description="操作人"),
        x_operate_time: str = Header(..., description="操作时间戳头")  # 动态时间头
    ) -> Dict[str, Any]:
        """批量更新商品状态"""
        pass


# ------------------------------
# 2. 完整调用示例（含Session和Header用法）
# ------------------------------
async def feign_advanced_demo():
    client = ProductServiceClient()

    # 场景1: 动态Header和Cookie
    reviews = await client.get_product_reviews(
        product_id=10086,
        status="APPROVED",
        x_auth_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # 动态令牌
        session_id="sid_123456"  # Cookie
    )
    print(f"场景1 - 评价数: {reviews.get('total', 0)}")

    # 场景3: 动态生成签名头（直接通过Header参数传递）
    import hashlib
    product_data = {
        "name": "无线蓝牙耳机",
        "price": 299.99,
        "stock": 500
    }
    # 生成签名（业务逻辑）
    sign_str = f"{product_data['name']}_{product_data['price']}_secret"
    signature = hashlib.md5(sign_str.encode()).hexdigest()
    # 传递签名头
    new_product = await client.create_product(
        product_data=product_data,
        x_signature=signature  # 动态签名通过Header参数传入
    )
    print(f"场景3 - 商品ID: {new_product.get('id')}")

    # 场景4: 分片上传（通过x_chunked头控制）
    product_id = new_product.get('id')
    if product_id:
        upload_result = await client.upload_product_image(
            product_id=product_id,
            file_paths=["/tmp/main.jpg", "/tmp/detail.jpg"],
            image_type="detail",
            x_chunked=True  # 启用分片上传
        )
        print(f"场景4 - 上传图片数: {len(upload_result.get('image_urls', []))}")
