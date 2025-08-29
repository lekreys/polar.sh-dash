import gradio as gr
import requests
import json
import os
from typing import Dict, Any, List, Optional, Tuple
import datetime
from dataclasses import dataclass
import re


class PolarAPI:
    """Polar.sh API client for the demo app"""

    def __init__(self, access_token: str, sandbox: bool = True):
        self.access_token = access_token

        self.base_url = "https://sandbox-api.polar.sh/v1" if sandbox else "https://api.polar.sh/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Polar API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                return {"error": f"Unsupported method {method}"}

            response.raise_for_status()
            if response.text.strip() == "":
                return {"status": response.status_code}
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "body": getattr(e.response, 'text', None)
            }


    def list_organizations(self) -> Dict:
        return self._make_request("GET", "/organizations/")

    def get_organization(self, organization_id: str) -> Dict:
        return self._make_request("GET", f"/organizations/{organization_id}/")


    def list_products(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/products/", params)

    def create_product(self, name: str, description: str, type: str, prices: List[Dict]) -> Dict:
        data = {
            "name": name,
            "description": description,
            "type": type,
            "prices": prices
        }
        return self._make_request("POST", "/products/", data)

    def get_product(self, product_id: str) -> Dict:
        return self._make_request("GET", f"/products/{product_id}/")

    def create_checkout(self, product_ids: List[str], success_url: str,
                        customer_email: str = None,
                        allow_discount_codes: bool = True,
                        require_billing_address: bool = False,
                        is_business_customer: bool = False) -> Dict:
        data = {
            "products": product_ids,
            "success_url": success_url,
            "allow_discount_codes": allow_discount_codes,
            "require_billing_address": require_billing_address,
            "is_business_customer": is_business_customer
        }
        if customer_email:
            data["customer_email"] = customer_email
        return self._make_request("POST", "/checkouts/", data)

    def list_subscriptions(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/subscriptions/", params)

    def get_subscription(self, subscription_id: str) -> Dict:
        return self._make_request("GET", f"/subscriptions/{subscription_id}/")

    def list_orders(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/orders/", params)

    def get_order(self, order_id: str) -> Dict:
        return self._make_request("GET", f"/orders/{order_id}/")

    def list_benefits(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/benefits/", params)

    def create_benefit(self, organization_id: str, type: str, description: str, properties: Dict) -> Dict:
        data = {
            "organization_id": organization_id,
            "type": type,
            "description": description,
            "properties": properties
        }
        return self._make_request("POST", "/benefits/", data)

    def list_customers(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/customers/", params)

    def list_webhook_endpoints(self, organization_id: str = None) -> Dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self._make_request("GET", "/webhooks/endpoints/", params)

    def create_webhook_endpoint(self, organization_id: str, url: str, events: List[str]) -> Dict:
        data = {
            "organization_id": organization_id,
            "url": url,
            "events": events
        }
        return self._make_request("POST", "/webhooks/endpoints/", data)


polar_api: Optional[PolarAPI] = None


def initialize_polar_api(access_token: str, use_sandbox: bool = True):
    global polar_api
    if not access_token:
        return "Access token is required"

    try:
        polar_api = PolarAPI(access_token, sandbox=use_sandbox)
        orgs = polar_api.list_organizations()
        if "error" in orgs:
            return f"ailed to connect: {orgs.get('error')} | body: {orgs.get('body')}"
        return "Connected to Polar"
    except Exception as e:
        return f"Error initializing API: {str(e)}"


def format_json_output(data: Dict) -> str:
    if isinstance(data, dict) and "error" in data:
        pretty_body = ""
        if data.get("body"):
            pretty_body = f"\nResponse body: {data['body']}"
        return f"Error: {data['error']} (status: {data.get('status_code')}){pretty_body}"
    return json.dumps(data, indent=2, ensure_ascii=False)



def get_organizations():
    if not polar_api:
        return "Please initialize API connection first"
    result = polar_api.list_organizations()
    return format_json_output(result)


def get_organization_details(org_id: str):
    if not polar_api:
        return " Please initialize API connection first"
    if not org_id:
        return "Organization ID is required"
    result = polar_api.get_organization(org_id)
    return format_json_output(result)



def get_products(org_id: str = None):
    if not polar_api:
        return "Please initialize API connection first"
    result = polar_api.list_products(org_id)
    return format_json_output(result)


def get_product_details(product_id: str):
    if not polar_api:
        return "Please initialize API connection first"
    if not product_id:
        return "Product ID is required"
    result = polar_api.get_product(product_id)
    return format_json_output(result)



UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")

def _is_uuid(s: str) -> bool:
    return bool(UUID_RE.match((s or "").strip()))

def _as_int_cents(v) -> Optional[int]:
    if v is None or str(v).strip() == "":
        return None
    try:
        n = int(float(str(v).strip()))
        return n
    except Exception:
        return None

def build_product_payload_simple(
    name: str,
    description: str,
    plan: str,              
    price_type: str,       
    fixed_amount: Optional[str],
    custom_min: Optional[str],
    custom_max: Optional[str],
    custom_preset: Optional[str],
    org_id: str,
    enable_metered: bool,
    meter_id: str,
    unit_amount: Optional[str],
    cap_amount: Optional[str],
) -> Dict[str, Any]:
    if not name or len(name.strip()) < 3:
        raise ValueError("Name minimal 3 karakter.")

    if plan == "one_time":
        recurring_interval = None
    elif plan in ("month", "year"):
        recurring_interval = plan
    else:
        raise ValueError("Plan tidak valid (one_time | month | year).")

    prices: List[Dict[str, Any]] = []
    if price_type not in ("fixed", "custom", "free"):
        raise ValueError("Tipe harga tidak valid (fixed | custom | free).")

    if price_type == "fixed":
        cents = _as_int_cents(fixed_amount)
        if cents is None or cents < 50:
            raise ValueError("Fixed price (cents) wajib diisi, min 50.")
        prices.append({
            "amount_type": "fixed",
            "price_currency": "usd",
            "price_amount": cents,
        })
    elif price_type == "custom":
        min_c = _as_int_cents(custom_min)
        max_c = _as_int_cents(custom_max)
        preset_c = _as_int_cents(custom_preset)
        if (min_c is not None and min_c < 50) or (max_c is not None and max_c < 50) or (preset_c is not None and preset_c < 50):
            raise ValueError("Custom price: minimum/maximum/preset harus ≥ 50 bila diisi.")
        if min_c is not None and max_c is not None and min_c > max_c:
            raise ValueError("Custom price: minimum tidak boleh > maximum.")
        price_obj = {"amount_type": "custom", "price_currency": "usd"}
        if min_c is not None:
            price_obj["minimum_amount"] = min_c
        if max_c is not None:
            price_obj["maximum_amount"] = max_c
        if preset_c is not None:
            price_obj["preset_amount"] = preset_c
        prices.append(price_obj)
    else:  
        prices.append({"amount_type": "free"})

    if enable_metered:
        if recurring_interval is None:
            raise ValueError("Produk one-time TIDAK boleh punya metered price.")
        if not meter_id or not _is_uuid(meter_id):
            raise ValueError("meter_id harus UUID valid.")
        if unit_amount is None or str(unit_amount).strip() == "":
            raise ValueError("unit_amount (cents) wajib diisi untuk metered.")
        metered = {
            "amount_type": "metered_unit",
            "meter_id": meter_id.strip(),
            "price_currency": "usd",
            "unit_amount": str(unit_amount).strip(),
        }
        cap = _as_int_cents(cap_amount)
        if cap is not None:
            if cap < 0:
                raise ValueError("cap_amount tidak boleh negatif.")
            metered["cap_amount"] = cap
        prices.append(metered)

    payload: Dict[str, Any] = {
        "name": name.strip(),
        "description": description if description else None,
        "recurring_interval": recurring_interval,  
        "prices": prices,
    }

    if org_id and org_id.strip():
        if not _is_uuid(org_id):
            raise ValueError("organization_id harus UUID valid.")
        payload["organization_id"] = org_id.strip()

    return payload


def create_product_simple_action(
    name: str,
    description: str,
    plan: str,
    price_type: str,
    fixed_amount: Optional[str],
    custom_min: Optional[str],
    custom_max: Optional[str],
    custom_preset: Optional[str],
    org_id: str,
    enable_metered: bool,
    meter_id: str,
    unit_amount: Optional[str],
    cap_amount: Optional[str],
) -> Tuple[str, str, str]:
    if not polar_api:
        return "Please initialize API connection first", "", ""

    try:
        payload = build_product_payload_simple(
            name, description, plan, price_type, fixed_amount, custom_min, custom_max, custom_preset,
            org_id, enable_metered, meter_id, unit_amount, cap_amount
        )
    except Exception as e:
        return f"{e}", "", ""

    url = f"{polar_api.base_url}/products/"
    headers = {**polar_api.headers, "Accept": "application/json"}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text}
        status = f"{r.status_code} {r.reason or ''}".strip()
    except requests.RequestException as e:
        return f"❌ Request error: {e}", "", ""

    return status, json.dumps(body, indent=2, ensure_ascii=False)

def generate_curl_simple_action(
    name: str,
    description: str,
    plan: str,
    price_type: str,
    fixed_amount: Optional[str],
    custom_min: Optional[str],
    custom_max: Optional[str],
    custom_preset: Optional[str],
    org_id: str,
    enable_metered: bool,
    meter_id: str,
    unit_amount: Optional[str],
    cap_amount: Optional[str],
) -> Tuple[str, str, str]:
    if not polar_api:
        dummy_base = "https://sandbox-api.polar.sh/v1"
    try:
        payload = build_product_payload_simple(
            name, description, plan, price_type, fixed_amount, custom_min, custom_max, custom_preset,
            org_id, enable_metered, meter_id, unit_amount, cap_amount
        )
    except Exception as e:
        return f"❌ {e}", "", ""

    return "DRY RUN — cURL generated only", json.dumps(payload, indent=2, ensure_ascii=False), 



def create_checkout_session(product_ids: str, success_url: str, customer_email: str = None,
                            allow_discount_codes: bool = True, require_billing_address: bool = False,
                            is_business_customer: bool = False):
    if not polar_api:
        return "Please initialize API connection first"

    if not all([product_ids, success_url]):
        return "Product IDs and success URL are required"

    try:
        product_list = [pid.strip() for pid in product_ids.split(",") if pid.strip()]
        if not product_list:
            return "At least one product ID is required"
    except:
        return "Invalid product IDs format. Use comma-separated list"

    result = polar_api.create_checkout(product_list, success_url, customer_email,
                                       allow_discount_codes, require_billing_address, is_business_customer)
    return format_json_output(result)



def get_subscriptions(org_id: str = None):
    if not polar_api:
        return "Please initialize API connection first"
    result = polar_api.list_subscriptions(org_id)
    return format_json_output(result)

def get_subscription_details(subscription_id: str):
    if not polar_api:
        return "Please initialize API connection first"
    if not subscription_id:
        return "Subscription ID is required"
    result = polar_api.get_subscription(subscription_id)
    return format_json_output(result)


def get_orders(org_id: str = None):
    if not polar_api:
        return "❌ Please initialize API connection first"
    result = polar_api.list_orders(org_id)
    return format_json_output(result)

def get_order_details(order_id: str):
    if not polar_api:
        return "❌ Please initialize API connection first"
    if not order_id:
        return "❌ Order ID is required"
    result = polar_api.get_order(order_id)
    return format_json_output(result)



def get_benefits(org_id: str = None):
    if not polar_api:
        return "❌ Please initialize API connection first"
    result = polar_api.list_benefits(org_id)
    return format_json_output(result)

def create_new_benefit(org_id: str, benefit_type: str, description: str, properties_json: str):
    if not polar_api:
        return "❌ Please initialize API connection first"
    if not all([org_id, benefit_type, description]):
        return "❌ Organization ID, type, and description are required"
    try:
        properties = json.loads(properties_json) if properties_json else {}
    except json.JSONDecodeError:
        return "❌ Invalid JSON in properties field"
    result = polar_api.create_benefit(org_id, benefit_type, description, properties)
    return format_json_output(result)


# =========================

def get_customers(org_id: str = None):
    if not polar_api:
        return "❌ Please initialize API connection first"
    result = polar_api.list_customers(org_id)
    return format_json_output(result)


def get_webhook_endpoints(org_id: str = None):
    if not polar_api:
        return "❌ Please initialize API connection first"
    result = polar_api.list_webhook_endpoints(org_id)
    return format_json_output(result)

def create_webhook_endpoint(org_id: str, url: str, events: str):
    if not polar_api:
        return "❌ Please initialize API connection first"
    if not all([org_id, url, events]):
        return "❌ Organization ID, URL, and events are required"
    try:
        event_list = [e.strip() for e in events.split(",") if e.strip()]
    except:
        return "❌ Invalid events format. Use comma-separated list"
    result = polar_api.create_webhook_endpoint(org_id, url, event_list)
    return format_json_output(result)


def create_gradio_app():
    with gr.Blocks(title="Polar.sh Complete API Demo", theme=gr.themes.Soft()) as app:
        gr.HTML("""
        <div style="text-align: center; padding: 20px;">
            <h1>COBA POLAR.SHH</h1>
        </div>
        """)

        with gr.Tab("API Setup"):
            gr.Markdown("## Polar API Connection")

            with gr.Row():
                access_token_input = gr.Textbox(
                    label="Access Token",
                    type="password",
                    placeholder="polar_at_... / org token",
                    info="Your Polar access token"
                )
                use_sandbox = gr.Checkbox(
                    label="Sandbox",
                    value=True,
                    info="kalo testing"
                )

            init_btn = gr.Button("Connect", variant="primary")
            init_output = gr.Textbox(label="Connection Status", interactive=False)

            init_btn.click(
                initialize_polar_api,
                inputs=[access_token_input, use_sandbox],
                outputs=[init_output]
            )

        with gr.Tab("Organizations"):
            gr.Markdown("## Organization Management")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### List Organizations")
                    list_orgs_btn = gr.Button("Get Organizations")
                    orgs_output = gr.Textbox(label="Organizations", lines=10)

                with gr.Column():
                    gr.Markdown("### Get Organization Details")
                    org_id_input = gr.Textbox(label="Organization ID", placeholder="uuid-org")
                    get_org_btn = gr.Button("Get Organization")
                    org_details_output = gr.Textbox(label="Organization Details", lines=10)

            list_orgs_btn.click(get_organizations, outputs=[orgs_output])
            get_org_btn.click(get_organization_details, inputs=[org_id_input], outputs=[org_details_output])

        with gr.Tab("Products"):
            gr.Markdown("## Product Management")

            with gr.Row():
                with gr.Column():
                    products_org_id = gr.Textbox(label="Organization ID (optional)", placeholder="uuid-org")
                    list_products_btn = gr.Button("Get Products")
                    products_output = gr.Textbox(label="Products", lines=8)

                    gr.Markdown("### Get Product Details")
                    product_id_input = gr.Textbox(label="Product ID", placeholder="uuid-product")
                    get_product_btn = gr.Button("Get Product")
                    product_details_output = gr.Textbox(label="Product Details", lines=8)

                with gr.Column():
                    gr.Markdown("### Create Product")
                    name_txt = gr.Textbox(label="Product Name", placeholder="Pro Plan")
                    desc_txt = gr.Textbox(label="Description")

                    with gr.Row():
                        plan_radio = gr.Radio(
                            ["one_time", "month", "year"],
                            value="month",
                            label="Plan"
                        )
                        price_type_radio = gr.Radio(
                            ["fixed", "custom", "free"],
                            value="fixed",
                            label="Price Type"
                        )


                    with gr.Tab("Fixed"):
                        fixed_cents = gr.Number(label="price (cents)", value=999, precision=0)

                    with gr.Tab("Custom / PWYW"):
                        with gr.Row():
                            custom_min = gr.Number(label="minimum (cents)", precision=0)
                            custom_max = gr.Number(label="maximum (cents)", precision=0)
                            custom_preset = gr.Number(label="preset(cents)", precision=0)

        

                    with gr.Row():
                        create_btn = gr.Button("Create Product", variant="primary")

                    status_out = gr.Textbox(label="info")
                    resp_out = gr.Textbox(label="Response", lines=12)

                    inputs_create = [
                        name_txt, desc_txt, plan_radio, price_type_radio,
                        fixed_cents, custom_min, custom_max, custom_preset,
                    ]

                    create_btn.click(
                        create_product_simple_action,
                        inputs=inputs_create,
                        outputs=[status_out, resp_out,]
                    )

                  

            list_products_btn.click(get_products, inputs=[products_org_id], outputs=[products_output])
            get_product_btn.click(get_product_details, inputs=[product_id_input], outputs=[product_details_output])

        with gr.Tab("Checkout"):
            gr.Markdown("## Checkout Session Management")

            with gr.Column():
                gr.Markdown("### Create Checkout Session")

                checkout_product_ids = gr.Textbox(
                    label="Product IDs (comma-separated)",
                    placeholder="uuid-prod-1, uuid-prod-2",
                )
                checkout_success_url = gr.Textbox(
                    label="Success URL",
                    placeholder="https://yoursite.com/success",
                    value="https://example.com/success"
                )
                checkout_email = gr.Textbox(label="Customer Email (optional)", placeholder="customer@example.com")

                with gr.Row():
                    allow_discount_codes = gr.Checkbox(label="Allow Discount Codes", value=True)
                    require_billing_address = gr.Checkbox(label="Require Billing Address", value=False)
                    is_business_customer = gr.Checkbox(label="Is Business Customer", value=False)

                create_checkout_btn = gr.Button("Create Checkout Session", variant="primary")
                checkout_output = gr.Textbox(label="Checkout Session", lines=12)

            create_checkout_btn.click(
                create_checkout_session,
                inputs=[checkout_product_ids, checkout_success_url, checkout_email,
                        allow_discount_codes, require_billing_address, is_business_customer],
                outputs=[checkout_output]
            )

        with gr.Tab("Subscriptions"):
            gr.Markdown("## Subscription Management")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### List Subscriptions")
                    subs_org_id = gr.Textbox(label="Organization ID (optional)", placeholder="uuid-org")
                    list_subs_btn = gr.Button("Get Subscriptions")
                    subs_output = gr.Textbox(label="Subscriptions", lines=10)

                with gr.Column():
                    gr.Markdown("### Get Subscription Details")
                    sub_id_input = gr.Textbox(label="Subscription ID", placeholder="uuid-subscription")
                    get_sub_btn = gr.Button("Get Subscription")
                    sub_details_output = gr.Textbox(label="Subscription Details", lines=10)

            list_subs_btn.click(get_subscriptions, inputs=[subs_org_id], outputs=[subs_output])
            get_sub_btn.click(get_subscription_details, inputs=[sub_id_input], outputs=[sub_details_output])

        with gr.Tab("Orders"):
            gr.Markdown("## Order Management")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### List Orders")
                    orders_org_id = gr.Textbox(label="Organization ID (optional)", placeholder="uuid-org")
                    list_orders_btn = gr.Button("Get Orders")
                    orders_output = gr.Textbox(label="Orders", lines=10)

                with gr.Column():
                    gr.Markdown("### Get Order Details")
                    order_id_input = gr.Textbox(label="Order ID", placeholder="uuid-order")
                    get_order_btn = gr.Button("Get Order")
                    order_details_output = gr.Textbox(label="Order Details", lines=10)

            list_orders_btn.click(get_orders, inputs=[orders_org_id], outputs=[orders_output])
            get_order_btn.click(get_order_details, inputs=[order_id_input], outputs=[order_details_output])

        with gr.Tab("Customers"):
            gr.Markdown("## Customer Management")

            with gr.Column():
                gr.Markdown("### List Customers")
                customers_org_id = gr.Textbox(label="Organization ID (optional)", placeholder="uuid-org")
                list_customers_btn = gr.Button("Get Customers")
                customers_output = gr.Textbox(label="Customers", lines=15)

            list_customers_btn.click(get_customers, inputs=[customers_org_id], outputs=[customers_output])

     
    return app


if __name__ == "__main__":
    # Create and launch the app
    app = create_gradio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
