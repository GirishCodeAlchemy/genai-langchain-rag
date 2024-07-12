from langchain.memory import ConversationBufferMemory


class LimitedConversationBufferMemory(ConversationBufferMemory):
    def __init__(self, memory_key="history", input_key="input", max_token_limit=7500):
        super().__init__(memory_key=memory_key, input_key=input_key, max_token_limit=max_token_limit)

    def load_memory(self):
        while self.token_count() > 6000 and self.buffer:
            print("*******", self.buffer, self.token_count())
            self.buffer.pop(0)
        return self.buffer

    def token_count(self):
         return sum(len(conversation["message"].split()) for conversation in self.buffer)