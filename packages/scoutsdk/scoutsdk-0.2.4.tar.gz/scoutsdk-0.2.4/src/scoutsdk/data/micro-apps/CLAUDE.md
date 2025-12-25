# Scout Micro-App

React/TypeScript application embedded in a Scout assistant.

## Development

```bash
make dependencies  # Install packages
make dev           # Dev server at localhost:5173
make build         # Production build
make format        # Format code
make check         # Lint & type check
```

## Key Packages

- `@mirego/scout-api` - Scout API client
- `@mirego/scout-chat` - UI components and hooks

## Essential Patterns

### Context Access
```typescript
import { useScoutAppContext } from '@mirego/scout-chat';
const { conversation_id, assistant_id, language } = useScoutAppContext();
```

### Chat Completion
```typescript
import { chat } from '@mirego/scout-api';
const response = await chat.chatCompletion({
  messages: [{ role: 'user', content: 'Hello' }],
  model: 'gpt-4o-mini',
});
```

### File Upload
```typescript
import { getSignedUploadUrl, uploadFile } from '@mirego/scout-api';

const { data } = await getSignedUploadUrl(conversation_id, { file_path: filename });
await uploadFile(conversation_id, filename, file, (progress) => {
  console.log(Math.round(progress.progress! * 100));
});
```

### Execute Backend Function
```typescript
import { executeAssistantCustomFunction } from '@mirego/scout-api';

await executeAssistantCustomFunction(
  assistant_id,
  'my_function_name',
  { param1: 'value' },
  conversation_id
);
```

### Sync State with Backend
```typescript
import { useConversationQuery } from '@mirego/scout-chat';
import { updateConversationUserData } from '@mirego/scout-api';

// Poll for updates
const { data } = useConversationQuery({ conversationId, refetchInterval: 1000 });
const userData = data?.user_data;

// Update from frontend
await updateConversationUserData(conversation_id, { step: 'processing' });
```

### Internationalization
```typescript
import { useScoutTranslation } from './hooks/use-scout-translation';
const { t } = useScoutTranslation();
// Strings in src/locales/strings.json
```

## UI Components (from @mirego/scout-chat)

- `MicroAppHeader` - App header with logo
- `MicroAppFileUpload` - File dropzone
- `MicroAppStepsContainer` / `MicroAppStep` - Progress steps
- `MicroAppFileInfo` - Display file info
- `MicroAppNewConversationButton` - Reset conversation

**The examples above are only a small sample.** You MUST explore `node_modules/@mirego/scout-api/src/` and `node_modules/@mirego/scout-chat/src/` to discover all available components, hooks, and APIs before implementing features.

## Project Structure

```
src/
├── App.tsx           # Main component
├── main.tsx          # Entry with ScoutApp wrapper
├── hooks/            # Custom hooks
├── locales/          # i18n strings (strings.json)
├── types.ts          # TypeScript types
└── index.css         # Styles
```

## Guidelines

- Use TypeScript strictly (avoid `any`)
- Handle loading and error states
- Use scout-chat components for consistent UX
- Test locally with `make dev` before building

## API Documentation

[Scout API Postman Collection](https://files.scout.mirego.com/external-services/Scout%20API.postman_collection.json)
