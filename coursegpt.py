from providers.utils.protocol import GenerationClient
from prompts import SUBTOPIC_TO_COURSE_CONTENT, TOPIC_TO_OUTLINE, ANSWER_DOUBT
import re, asyncio

class CourseGPT():
    @staticmethod
    def digest_outline(response):
        """
        Convert LLM Generated Outline to a consumable format.
        
        Format:
        ```
        [
            {
                "topic": "Topic 1",
                "subtopics": [
                    "Subtopic 1",
                    "Subtopic 2",
                    "Subtopic 3"
                ]
            },
            {
                "topic": "Topic 2",
                "subtopics": [
                    "Subtopic 1",
                    "Subtopic 2",
                    "Subtopic 3"
                ]
            }
        ]
        ```
        """
        subtopic_pattern = re.compile(r"&&(.*?)&&")
        segments = [segment.strip() for segment in response.split("$$") if segment.strip()]

        output = []
        
        for i in range(0, len(segments), 2):
            topic_name = segments[i]
            subtopics_content = segments[i + 1] if i + 1 < len(segments) else ""
            subtopics = [
                m.group(1).strip() for m in subtopic_pattern.finditer(subtopics_content)
            ]
            
            topic_name = re.sub(r'Unit \d+: ', '', topic_name)
            subtopics = [re.sub(r'Subheading \d+: ', '', subtopic) for subtopic in subtopics]
            subtopics_dicts = [{"name": subtopic, "text": "Generating..."} for subtopic in subtopics]

            output.append({"topic": topic_name, "subtopics": subtopics_dicts})

        return output

    @staticmethod
    def conv_h_to_str(topics):
        """
        Convert topic data to a formatted string representation.
        """
        out = ""
        for index, item in enumerate(topics):
            out += f"{index+1}. {item['topic']}\n"
            for s_index, subtopic in enumerate(item['subtopics']):
                out += f"\t{index+1}.{s_index+1}. {subtopic['name']}\n"
        return out
    
    @staticmethod
    async def generate_outline(topic, client: GenerationClient):
        messages = [
            {
                "role": "system",
                "content": TOPIC_TO_OUTLINE.format(topic=topic)
            },
            {
                "role": "user",
                "content": topic
            }
        ]
        response = await client.create(messages, async_mode=True)
        outline = CourseGPT.digest_outline(response)
        return outline

    @staticmethod
    async def generate_all_subtopics_generator_parallelized(outline, topic, client: GenerationClient):
        formatted_outline = CourseGPT.conv_h_to_str(outline)
        
        async def generate_content_task(topic, topic_number, subtopic_number):
            messages = [
                {
                    "role": "system",
                    "content": SUBTOPIC_TO_COURSE_CONTENT.format(formatted_outline=formatted_outline, topic=topic)
                },
                {
                    "role": "user",
                    "content": "Current section number: {topic_number}.{subtopic_number}".format(topic_number=topic_number, subtopic_number=subtopic_number)
                }
            ]
            content = await client.create(messages, async_mode=True)
            return { "topic_number": topic_number, "subtopic_number": subtopic_number, "content": content }

        tasks = []
        
        for topic_number, topic_data in enumerate(outline, start=1):
            for subtopic_number, subtopic_data in enumerate(topic_data['subtopics'], start=1):
                task = generate_content_task(topic, topic_number, subtopic_number)
                tasks.append(task)
        
        # Dispatch all tasks concurrently and yield results as they are resolved
        for result in asyncio.as_completed(tasks):
            yield await result
            
    @staticmethod
    async def generate_all_subtopics_generator_sequential(outline, topic, client: GenerationClient):
        formatted_outline = CourseGPT.conv_h_to_str(outline)
        
        async def generate_content(topic, topic_number, subtopic_number):
            messages = [
                {
                    "role": "system",
                    "content": SUBTOPIC_TO_COURSE_CONTENT.format(formatted_outline=formatted_outline, topic=topic)
                },
                {
                    "role": "user",
                    "content": f"Current section number: {topic_number}.{subtopic_number}"
                }
            ]
            return await client.create(messages, async_mode=True)

        for topic_number, topic_data in enumerate(outline, start=1):
            for subtopic_number, subtopic_data in enumerate(topic_data['subtopics'], start=1):
                content = await generate_content(topic, topic_number, subtopic_number)
                yield {"topic_number": topic_number, "subtopic_number": subtopic_number, "content": content}
                
    @staticmethod
    async def answer_doubt(content, doubt, outline, client: GenerationClient):
        formatted_outline = CourseGPT.conv_h_to_str(outline)
        messages = [
            {
                "role": "system",
                "content": ANSWER_DOUBT.format(formatted_outline=formatted_outline, content=content)
            },
            {
                "role": "user",
                "content": doubt
            }
        ]
        response = await client.create(messages, async_mode=True)
        return response