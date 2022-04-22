import asyncio
import time
from shimeji import ChatBot
from shimeji.model_provider import ModelProvider, Sukima_ModelProvider, TextSynth_ModelProvider, ModelGenRequest, ModelGenArgs, ModelSampleArgs
from shimeji.preprocessor import ContextPreprocessor
from shimeji.postprocessor import NewlinePrunerPostprocessor
from shimeji.memorystore_provider import PostgreSQL_MemoryStoreProvider, Memory
from shimeji.memory import array_to_str, memory_context, str_to_numpybin

async def main():
    ms = PostgreSQL_MemoryStoreProvider(database_uri='postgresql+asyncpg://postgresql:postgresql@0.0.0.0:2027/eliza')

    gen_args = ModelGenArgs(max_length=100, min_length=1, eos_token_id=198)
    sample_args = ModelSampleArgs(temp=0.75, top_p=0.725, typical_p=0.95, rep_p=1.125)
    model_args = ModelGenRequest(model='convo-6B-8bit', prompt='', sample_args=sample_args, gen_args=gen_args)

    model_provider = Sukima_ModelProvider(
        'http://192.168.0.147:8000',
        username='username',
        password='password',
        args=model_args
    )

    chatbot = ChatBot(
        name='Patchouli Knowledge',
        model_provider=model_provider,
        preprocessors=[ContextPreprocessor()],
        postprocessors=[NewlinePrunerPostprocessor()]
    )
    
    while True:
        try:
            entered = input('haru: ')
            if await ms.check_duplicates(text=entered, duplicate_ratio=0.8):
                print('duplicate')
            await ms.add(
                author_id=1337,
                author='haru',
                text=entered,
                encoding_model='convo-6B-8bit',
                encoding=array_to_str(await model_provider.hidden_async(model_args, 'haru: ' + entered, layer=-1)),
            )
            
            response = await chatbot.respond_async('haru:' + entered, push_chain=True)
            print(f'Patchouli Knowledge: {response}')
            await ms.add(
                author_id=1227,
                author='Patchouli Knowledge',
                text=response,
                encoding_model='convo-6B-8bit',
                encoding=array_to_str(await model_provider.hidden_async(model_args, 'Patchoulli Knowledge: '+response, layer=-1)),
            )

            print('\n\n--Memories--')
            memories = await ms.get()
            print(memory_context(memories[-1], memories, 2, 10))
            print('\n\n')
            
        except KeyboardInterrupt:
            memories = await ms.get(created_after=0) # get all memories
            print(f'\n\n--Memories ({await ms.count()}) --')
            for memory in memories:
                print(f'{memory.created_at} - {memory.author}: {memory.text} - {len(str_to_numpybin(memory.encoding))}')
                await ms.delete(memory=memory) # delete memory
            print('--End of Memories--\n')
            break

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())