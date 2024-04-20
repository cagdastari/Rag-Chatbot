from langchain_community.embeddings import OpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import datetime
from openai import OpenAI
# from get_ip import get_remote_ip
from sentence_transformers import CrossEncoder
import numpy as np
from langchain.docstore.document import Document
import random
import logging

#OPENAI KEY
os.environ["OPENAI_API_KEY"] = "************************************"
#EMBEDDING
embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
#filter
# embeddings_filter = EmbeddingsFilter(embeddings=embedding, similarity_threshold=0.76)
# redundant_filter = EmbeddingsRedundantFilter(embeddings=embedding,similarity_threshold=0.5)

#LOAD DOCS
loader = Docx2txtLoader("./YOUR_DOC.docx")
documents = loader.load()

#SPLIT DOC INTO CHUNKS
text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=50) 
splits = text_splitter.split_documents(documents)

#DEFINE VECTOR DB (FAISS AND BM25)
faiss_vectorstore = FAISS.from_documents(splits, embedding)
faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 4})

bm25_retriever  = BM25Retriever.from_documents(splits)
bm25_retriever.k = 4

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
)
#CROSS ENCODING TO GET MORE RELATED CHUNKS
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

#RETURN PROMPTED CHUNKS (READY TO PUT IN LLM)
def augment_prompt(query: str):
    
    ordered_retrieve = []
    answers = ensemble_retriever.get_relevant_documents(query)
    content = [doc.page_content for doc in answers]
    # print(len(content))
    # print(answers[0].page_content)
    pairs = [[query, doc] for doc in content]
    scores = cross_encoder.predict(pairs)

    for o in np.argsort(scores)[::-1]:
        # print(o+1)
        if len(ordered_retrieve)<4:
            ordered_retrieve.append(content[o])
        
    # context = '\n'.join(content)
    context = '\n'.join(ordered_retrieve)

    print(context)


    augmented_prompt ={"role": "system", "content": f""" 
    You are the cheerful hr assistant of Axa, named Şans.\n
    Your task is having short conversations with user and providing information based on the given context.\n
    Don't use a formal language, talk like talking with a close friend.\n
    If the user asks 'sen kimsin', simply say 'Ben Axa'nın neşeli ik asistanı Şans'ım'.\n
    If the user asks 'nasılsın', simply say 'İyiyim teşekkür ederim, sen nasılsın?'.\n
    If the user wants you to make joke, tell a short funny joke.\n

    context: {context}\n
    This context consists of question-answer couples taken from the document according to the user's question.\n
    Not all of them may be directly related to the question asked.\n 
    Your task is finding question related parts of the context and giving the most accurate answer by evaluating the information and the question.\n 

    If the user asks what you can do or asks about your features, give brief summary of the context as examples of what you can do.\n
    If the asked informations is not provided in context, respond with: 'Bu konuda bilgi sahibi değilim, İK iş ortağına danışabilirsin.'\n

    Avoid giving informations that is not provided in the context.\n
    Avoid using prior knowledge.\n

    Brief answer in Turkish:"""}

    # Avoid giving informations that is not provided in the context.\n
    # Avoid using prior knowledge.\n

    # NEVER give informations that is not provided in the context.\n
    # NEVER make assumptions when giving answers.\n
    # NEVER give answers using prior knowledge.\n
    
    return augmented_prompt


class responser:
    client = OpenAI()
    emojies = [' :feet:',' :paw_prints:',' :cat2:',' :cat:',' :smile_cat:',' :smiley_cat:','']
    miyav = [' miyuv','',' miyav',' miyaav',' miyiv','','','','',' patilerim klavyenin üzerinde hazır bekliyor',' tüylü kulaklarım sana açık!',' Pati pati yardımcı olmaya hazırım!']
    # my_thread = client.beta.threads.create()

    def get_response(self,user_input,thread):
        #RETRIEVE THE FINE TUNED ASSISTANT
        my_assistant = self.client.beta.assistants.retrieve("asst_6eeLs26fWVpAxbcoz5yoLCBQ")

        #CREATE UNIQUE THREAD FOR IP 
        my_thread_message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content= user_input,
        )
        #RUN WITH GIVEN THREAD AND ASSISTANT 
        my_run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=my_assistant.id,
            # instructions="Give answers like cat in Turkish"
        )

        #PROCESS ASSITANT OUTPUT STATUS AND GET RESPPONSE
        st = datetime.datetime.now()
        while my_run.status in ["queued", "in_progress"]:
            keep_retrieving_run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=my_run.id
            )
            print(f"Run status: {keep_retrieving_run.status}")
        
            if keep_retrieving_run.status == "completed":
                print("\n")
        
                # Step 6: Retrieve the Messages added by the Assistant to the Thread
                all_messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
        
                print("------------------------------------------------------------ \n")
                assistant_message = all_messages.data[0].content[0].text.value
                print(f"User: {my_thread_message.content[0].text.value}")
                print(f"Assistant: {all_messages.data[0].content[0].text.value}")

        
                break
            elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
                pass
            else:
                print(f"Run status: {keep_retrieving_run.status}")
                assistant_message = 'Server kaynaklı bir hata oluştu.'
                break
        ed = datetime.datetime.now()
        tt = ed-st
        tt = tt.seconds
        print(f"THREAD ID : {thread.id}")
        print(f"{tt} SECONDS")
        last_message = assistant_message + random.choice(self.miyav) + random.choice(self.emojies)

        #WRITE INTO LOG FILE
        logging.basicConfig(filename='log.log',encoding='utf-8',format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
        logging.info(f'passed_time:{tt}-user_input:{user_input}-ai_answer:{assistant_message}')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info(f"user_input:{user_input}-ai_response:{assistant_message}")

        return last_message

# from fastapi import FastAPI
# from pydantic import BaseModel

# class UserInput(BaseModel):
#     input: str

# r = responser()
# app = FastAPI()

# @app.post("/ask_question/")
# def give_response(user_input:UserInput):
#     try:
#         resp = r.get_response(str(user_input))
#         return resp  

#     except Exception as e:
#         print(e)
#         return e

# if __name__ == "__main__":
#     import uvicorn
 
#     uvicorn.run(app, host="127.0.0.1", port=8000)  

# r = responser()
# # queries = ['CEO Talks diye bir şey organize edilmiş, ne bu, ne yapılıyor burada?,','idari işler hangi konularda yardımcı olur','İK iş ortağına nasıl ulaşırım','nasılsın','neler yapabilirsin','hamilelere izin veriliyor mu','yeni evlenenlere hediye veriliyor mu','maaşlar hangi bankadan yatıyor','ik ya nasıl ulaşabilirim','sen kimsin?','müşteri hizmetleri','excom kimlerden oluşuyor','Dün mezun oldum, YL bitti, bilgilrimi nasıl güncelleyeceğim','Yıllık iznimi kullanmazsam nolur']

# import time
# while True:
# # f = open("sontest2.txt", "a",encoding='utf-8')
# # for query in queries:
#     user= str(input('QUERY :'))
#     st = datetime.datetime.now()
#     cevap,retrieve_time = r.get_response(user)
#     end = datetime.datetime.now()
#     total_time = end-st
#     # # print('QUERY : '+query)
#     # f.write('QUERY : '+query+'\n')
#     # f.write('response time : '+str(total_time.seconds)+' seconds'+'\n')
#     # f.write('RESPONSE : '+cevap+'\n')
#     print('response time : '+str(total_time.seconds)+' seconds')
#     print('RESPONSE : '+cevap)
#     # time.sleep(3)
# f.close()

# file = open('./Tes.txt',"r",encoding="utf-8")
# lines = file.readlines()

# f = open('sontest.txt',"a",encoding='utf-8')
# for line in lines:
#     if '+' in line:
#         cevap,retrieve_time = r.get_response(line[:-2])
#         f.write(line[:-2]+"\n")
#         f.write(cevap+"\n"+"\n")
# f.close()