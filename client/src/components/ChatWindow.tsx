import React, { useState } from 'react';
import { Outline } from './types';
import { BASEURL } from './config';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { ReactMarkdown } from 'react-markdown/lib/react-markdown'

const ChatWindow = ({ toggleChat, outline, showSubheading }: { toggleChat: () => void, outline: Outline, showSubheading: { topic: number, subtopic: number } }) => {

    const [stage, setStage] = useState<"NODOUBT" | "GENERATING" | "DONE">("NODOUBT");
    const [doubt, setDoubt] = useState<string>("");
    const [answer, setAnswer] = useState<string>("");

    
    const handleAskDoubt = async () => {
        if (stage === "DONE") {
            setAnswer("");
        }
        setStage("GENERATING");
        const content = outline.items[showSubheading.topic].subtopics[showSubheading.subtopic].text
        const response = await fetch(`${BASEURL}/api/ask_doubt`, {
            method: "POST",
            body: JSON.stringify({ doubt, outline, content }),
            headers: {
                "Content-Type": "application/json"
            }
        });
        if (response.ok) {
            const { answer } = await response.json();
            setAnswer(answer);
            setStage("DONE");
        }
    }

    return <>
        <div className='absolute flex-col flex border-2 border-violet-400 bg-white left-[calc(100%-450px)] top-[calc(100%-450px)] rounded-md h-[450px] w-[450px]'>
            <div className='absolute top-0 right-0 z-50'>
                <button className='ml-auto'>
                    <img src="/chatclose.svg" alt="" className='h-6 m-2' onClick={toggleChat} />
                </button>
            </div>
            <div className='relative flex-grow h-full px-2 py-4 overflow-y-scroll scrollbar-hidden'>
                {
                    doubt && stage !== "NODOUBT" && <div className='mb-2'>
                        <div className='font-bold'>
                            Question
                        </div>
                        <div>
                            {doubt}
                        </div>
                    </div>
                }
                {
                    stage === "GENERATING" && <div>
                        Thinking...!
                    </div>
                }
                {
                    answer && <div>
                        <div className='font-bold'>
                            Answer
                        </div>
                        <div className=''>
                            <ReactMarkdown
                                children={answer}
                                className={`prose`}
                                components={{
                                    code({node, inline, className, children, ...props}) {
                                        const match = /language-(\w+)/.exec(className || '')
                                        return !inline && match ? (
                                        <SyntaxHighlighter
                                            {...props}
                                            children={String(children).replace(/\n$/, '')}
                                            style={oneDark}
                                            language={match[1]}
                                            PreTag="div"
                                        />
                                        ) : (
                                        <code {...props} className={className}>
                                            {children}
                                        </code>
                                        )
                                    }
                                }}
                            />
                        </div>
                    </div>
                }
            </div>
            <div className='flex'>
                <input value={doubt} onChange={e => setDoubt(e.target.value)} type="text" placeholder='Ask anything' className='flex-grow px-2 border outline-none border-t-violet-600 rounded-bl-md' />
                <button onClick={handleAskDoubt} disabled={stage === "GENERATING"} className={`p-2 rounded-br-md ${stage === "GENERATING" ? "bg-neutral-700" : "bg-violet-600"}`}>
                    <img src="/ask.svg" alt="" className='h-6' />
                </button>
            </div>
        </div>
    </>
};

export default ChatWindow;
