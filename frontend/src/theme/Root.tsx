import React from 'react';
import { ChatProvider } from '@site/src/context/ChatContext';
import ChatWidget from '@site/src/components/ChatWidget';
import SelectionPopover from '@site/src/components/SelectionPopover';

/**
 * Root component wrapper for the entire Docusaurus site.
 *
 * This component persists across all SPA navigations, making it ideal for:
 * - Global state providers (ChatProvider)
 * - Persistent UI components (ChatWidget, SelectionPopover)
 * - Global event listeners
 *
 * @see https://docusaurus.io/docs/swizzling#wrapper-your-site-with-root
 */
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <ChatProvider>
      {children}
      <SelectionPopover />
      <ChatWidget />
    </ChatProvider>
  );
}
