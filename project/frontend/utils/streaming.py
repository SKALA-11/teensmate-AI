"""
Streaming Utility

스트리밍 어댑터 공용 유틸리티
"""

import asyncio
import threading
import queue

def sync_stream(async_gen):
    """
    비동기 제너레이터를 동기 제너레이터로 변환하는 어댑터.
    별도 스레드에서 asyncio 이벤트 루프를 실행하여 Streamlit 환경과 호환되게 합니다.
    """
    q = queue.Queue()
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def consume():
            try:
                async for item in async_gen:
                    q.put(item)
            except Exception as e:
                q.put(e)
            finally:
                q.put(StopIteration)
                
        loop.run_until_complete(consume())
        loop.close()
        
    t = threading.Thread(target=run_async)
    t.start()
    
    while True:
        item = q.get()
        if item is StopIteration:
            break
        if isinstance(item, Exception):
            raise item
        yield item
    t.join()
