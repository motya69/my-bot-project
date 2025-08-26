from bot.actions import render_tire_offers, render_wheels_offers

class MockBot:
    def __init__(self):
        self.messages = []
    def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))

def test_render_tire_offers():
    bot = MockBot()
    ctx = {
        "tire_offers": [
            {"title": "Michelin Primacy 4 (205/55 R16)", "subtitle": "Лето, Средний",
             "price": "12 000 ₽", "stock": 8, "url": "https://shop/tires/1"}
        ]
    }
    render_tire_offers(bot, chat_id=1, ctx=ctx)
    assert bot.messages, "render_tire_offers не отправил сообщений"
    assert "Michelin" in bot.messages[0][1]

def test_render_wheels_offers():
    bot = MockBot()
    ctx = {
        "wheel_offers": [
            {"title": "Replay FD110", "subtitle": "R17 7.0J 5x114.3 ET45 DIA 60.1",
             "price": "110 € / шт", "stock": 8, "url": "https://shop/wheels/1"}
        ]
    }
    render_wheels_offers(bot, chat_id=1, ctx=ctx)
    assert bot.messages, "render_wheels_offers не отправил сообщений"
    assert "Replay" in bot.messages[0][1]
