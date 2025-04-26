from aiogram.types import Message

async def send_grouped_blocks(message: Message, items: list[tuple], formatter: callable, block_size: int = 30):
    """
    Отправляет список items блоками по block_size, используя функцию formatter для форматирования.
    """
    blocks = [items[i:i+block_size] for i in range(0, len(items), block_size)]
    
    for block in blocks:
        text = "\n\n".join([formatter(item) for item in block])
        await message.answer(text, parse_mode="Markdown")
