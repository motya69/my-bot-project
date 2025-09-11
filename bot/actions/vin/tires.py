def tires_sizes_from_vin(bot, chat_id, ctx):
    vin = ctx.get("vin")
    print(f"[VIN TIRES] input={vin}", flush=True)

    # мок: подставляем тестовые размеры
    sizes = ["205/55 R16", "195/65 R15"]
    ctx["size_options"] = sizes

    if sizes:
        bot.send_message(chat_id, "Нашли размеры по VIN, выберите 👇")
    else:
        bot.send_message(chat_id, "❌ Размеры по VIN не найдены.")
