from ...core.app import get_app_state


async def handle_chat(message: str) -> bool:
    app = get_app_state()

    if not message or not message.strip():
        return True

    if app.rag_manager.connected:
        usage_stats = await app.rag_manager.send_message(message)

        if usage_stats:
            total_input_tokens = sum(
                u.get("input_tokens", 0) for u in usage_stats.get("usage", [])
            )
            total_output_tokens = sum(
                u.get("output_tokens", 0) for u in usage_stats.get("usage", [])
            )
            response_time = usage_stats.get("response_time", "N/A")
            queued_for = usage_stats.get("queue_time", "N/A")
            llm = usage_stats.get("llm", "N/A")
            app.ui.show_info(
                f"Tokens: {total_input_tokens} (in), {total_output_tokens} (out), "
                f"Response time: {response_time}, "
                f"Queued for: {queued_for}, "
                f"LLM: {llm}"
            )

        await app.update_status_bar()
    else:
        app.ui.show_error("Not connected to H2OGPTE. Use /register to connect first.")
        app.ui.show_info(
            "Example: /register https://your-h2ogpte-endpoint.com your-api-key"
        )

    return True
