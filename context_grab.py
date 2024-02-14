import time
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# simple context match system 
def context_match_simple(context_stack,chat):
    match_count = []
    chat = chat.split(" ")
    curr_list = []
    pos_count = 0
    for x in context_stack:
        counter = 0
        context_split = x.split(" ")
        for y in chat:
            if y in context_split:
                counter += 1
            else:
                pass
        pos_count += 1
        match_count.append([pos_count-1,counter])

    for x in match_count:
        if len(curr_list) == 0:
            curr_list.append(x)
        else:
            if x[1] > curr_list[0][1]:
                curr_list = []
                curr_list.append(x)
            elif x[1] == curr_list[0][1]:
                curr_list.append(x)
            else:
                pass
        
    return curr_list


def context_match_adv(stack,chat):
    # import the SentenceTransformer library
    print("context is being used")

    # load a pre-trained model
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    # encode the chat and stack sentences into vectors
    chat_vec = model.encode(chat)
    stack_vec = model.encode(stack)

    # compute the cosine similarity between the chat and each stack sentence
    similarity_scores = cosine_similarity([chat_vec], stack_vec)[0]

    # find the index of the highest scoring sentence in the stack
    best_index = similarity_scores.argmax()

    # save the highest scoring sentence as best_match
    best_match = stack[best_index]

    # print the best_match
    print(best_match)

    return(best_match)

		
	