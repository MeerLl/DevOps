def demo_sync_clients():
    print("=== Демонстрация синхронных клиентов ===")
    
    print("\n1. Клиент urllib:")
    urllib_client = UrllibUserClient()
    try:
        users = urllib_client.get_all_users()
        print(f"Найдено пользователей: {len(users)}")
    except Exception as e:
        print(f"Ошибка urllib: {e}")
    
    print("\n2. Клиент requests:")
    requests_client = RequestsUserClient()
    try:
        users = requests_client.get_all_users()
        print(f"Найдено пользователей: {len(users)}")

        if users:
            user = requests_client.get_user(users[0]['id'])
            print(f"Пользователь: {user}")
            
    except Exception as e:
        print(f"Ошибка requests: {e}")

async def demo_async_clients():
    """Демонстрация асинхронных клиентов"""
    print("\n=== Демонстрация асинхронных клиентов ===")
    
    print("\n3. Клиент httpx:")
    httpx_client = HttpxUserClient()
    try:
        await demo_httpx_client()
    except Exception as e:
        print(f"Ошибка httpx: {e}")
    
    print("\n4. Клиент aiohttp:")
    aiohttp_client = AiohttpUserClient()
    try:
        await demo_aiohttp_client()
    except Exception as e:
        print(f"Ошибка aiohttp: {e}")

if __name__ == "__main__":
    demo_sync_clients()
    
    asyncio.run(demo_async_clients())