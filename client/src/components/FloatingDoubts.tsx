
import React, { useState } from 'react';
import ChatWindow from './ChatWindow';
import { Outline } from './types';

const FloatingDoubts = ({ outline, showSubheading }: {outline: Outline, showSubheading: { topic: number, subtopic: number }}) => {
  const [showChat, setShowChat] = useState(false);

  const toggleChat = () => {
    setShowChat(!showChat);
  };

  return (
    <div className='absolute z-50 right-16 bottom-10'>
      {showChat ? <ChatWindow toggleChat={toggleChat} outline={outline} showSubheading={showSubheading} /> : null}
      <button onClick={toggleChat} className='p-3 rounded-full bg-violet-500'>
        <img src="/question.svg" alt="" className='h-10' />
      </button>
    </div>
  );
};

export default FloatingDoubts;
