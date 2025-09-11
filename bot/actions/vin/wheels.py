def wheels_params_from_vin(bot, chat_id, ctx):
    vin = ctx.get("vin")
    print(f"[VIN WHEELS] input={vin}", flush=True)

    # моковые параметры дисков
    params = {
        "wheel_r": "16",
        "wheel_j": "6.5",
        "wheel_pcd": "5x114.3",
        "wheel_et": "45",
        "wheel_dia": "66.1",
    }
    ctx.update(params)

    bot.send_message(chat_id, "Нашли параметры дисков по VIN ✅")
