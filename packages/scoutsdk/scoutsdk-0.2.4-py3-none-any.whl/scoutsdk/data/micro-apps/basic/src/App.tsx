import { ConversationMessage, chat } from '@mirego/scout-api';
import { Button, useScoutAppContext } from '@mirego/scout-chat';
import '@mirego/scout-chat/style.css';
import { useCallback, useState } from 'react';

const App = () => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleTestChat = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await chat.chatCompletion({
        messages: [
          {
            role: 'user',
            content: 'This is a test!',
          },
        ],
        model: 'gpt-5-mini',
      });
      setMessages(res.messages);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Button
        variant="primary"
        size="md"
        textSize="base"
        onClick={handleTestChat}
        isLoading={isLoading}
        disabled={isLoading}
      >
        Send 'This is a test' to the LLM
      </Button>
      <div>{messages.map(message => message.content).join('\n')}</div>
    </div>
  );
};

const WrappedApp = () => {
  const { conversation_id } = useScoutAppContext();
  return <App key={conversation_id} />;
};

export default WrappedApp;
