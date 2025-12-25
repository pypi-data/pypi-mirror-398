from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

from sycommon.synacos.feign_client import feign_client, feign_request
from sycommon.synacos.param import Body, Form, Query


# ------------------------------
# 请求模型（req）
# ------------------------------
class ProductCreateReq(BaseModel):
    """创建商品的请求模型"""
    name: str = Field(..., description="商品名称")
    category: str = Field(..., description="商品分类")
    price: float = Field(..., gt=0, description="商品价格（必须>0）")
    stock: int = Field(..., ge=0, description="库存（必须>=0）")
    attributes: Optional[Dict[str, str]] = Field(None, description="商品属性")


class BatchUpdateStatusReq(BaseModel):
    """批量更新状态的请求模型（表单提交）"""
    product_ids: str = Field(..., description="商品ID列表（逗号分隔）")
    status: str = Field(..., description="目标状态（如ON_SALE/OFF_SALE）")
    operator: str = Field(..., description="操作人")


# ------------------------------
# 响应模型（resp）
# ------------------------------
class ProductResp(BaseModel):
    """商品详情响应模型"""
    id: int = Field(..., description="商品ID")
    name: str = Field(..., description="商品名称")
    category: str = Field(..., description="分类")
    price: float = Field(..., description="价格")
    stock: int = Field(..., description="库存")
    created_at: str = Field(..., description="创建时间")


class PageResp(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总条数")
    items: List[ProductResp] = Field(..., description="商品列表")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页条数")


@feign_client(
    service_name="product-service",
    path_prefix="/api/v2",
    default_headers={"Accept": "application/json"}
)
class ProductServiceClient:
    # ------------------------------
    # 场景1: Pydantic 作为请求体（Body）
    # ------------------------------
    @feign_request("POST", "/products", timeout=15)
    async def create_product(
        self,
        # 使用 Pydantic 模型作为请求体
        product: ProductCreateReq = Body(..., description="商品信息")
    ) -> ProductResp:  # 响应自动解析为 ProductResp 模型
        """创建商品（Pydantic请求体 + Pydantic响应）"""
        pass

    # ------------------------------
    # 场景2: Pydantic 作为表单参数（Form）
    # ------------------------------
    @feign_request(
        "POST",
        "/products/batch-status",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    async def batch_update_status(
        self,
        # 使用 Pydantic 模型作为表单参数
        update_data: BatchUpdateStatusReq = Form(..., description="批量更新信息")
    ) -> Dict[str, Any]:  # 普通字典响应
        """批量更新商品状态（Pydantic表单）"""
        pass

    # ------------------------------
    # 场景3: 响应为分页模型（嵌套Pydantic）
    # ------------------------------
    @feign_request("GET", "/products", timeout=10)
    async def search_products(
        self,
        category: str = Query(..., description="商品分类"),
        page: int = Query(1, description="页码"),
        size: int = Query(10, description="每页条数")
    ) -> PageResp:  # 响应自动解析为 PageResp（嵌套 ProductResp）
        """搜索商品（Pydantic分页响应）"""
        pass


async def pydantic_feign_demo():
    client = ProductServiceClient()

    # 场景1: 创建商品（Pydantic请求体 + 响应）
    create_req = ProductCreateReq(
        name="无线蓝牙耳机",
        category="electronics",
        price=299.99,
        stock=500,
        attributes={"brand": "Feign", "battery_life": "24h"}
    )
    product = await client.create_product(product=create_req)
    # 直接使用 Pydantic 模型的属性
    print(f"创建商品: ID={product.id}, 名称={product.name}, 价格={product.price}")

    # 场景2: 批量更新（Pydantic表单）
    batch_req = BatchUpdateStatusReq(
        product_ids=f"{product.id},1002,1003",
        status="ON_SALE",
        operator="system"
    )
    batch_result = await client.batch_update_status(update_data=batch_req)
    print(f"批量更新成功: {batch_result.get('success_count')}个")

    # 场景3: 搜索商品（Pydantic分页响应）
    page_resp = await client.search_products(
        category="electronics",
        page=1,
        size=10
    )
    # 分页模型的属性和嵌套列表
    print(
        f"搜索结果: 共{page_resp.total}条，第1页商品: {[p.name for p in page_resp.items]}")
