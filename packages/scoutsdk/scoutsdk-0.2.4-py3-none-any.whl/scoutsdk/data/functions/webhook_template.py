from scoutsdk import scout, ScoutAPI


@scout.webhook(
    verification_signature_header_key="X-VERIFICATION-HEADER",
    assistant_secret_variable_key="SCOUT_ASSISTANT_SECRET"
)
def my_webhook():
    print("Hello from the webhook!")
    
    # For development, set SCOUT_API_URL and SCOUT_API_ACCESS_TOKEN in your environment variables or scout_context.json
    # When used by an assistant, URL and ACCESS_TOKEN are provided    
    api = ScoutAPI()
    # api.utils.get_document_text("file_to_path")

    # To access configured assistant variables or secrets, use:
    # scout.context["VARIABLE_NAME"]

    # Add your webhook logic here
    # You can access request data, process webhooks, etc.
    
    return {"status": "success", "message": "Webhook received"}