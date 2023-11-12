import { stages } from "./common"

export interface OutlineAPIResponse {
    items: {
        topic: string
        subtopics: {
            name: string
            text: string
        }[]
    }[]
}

export interface Outline {
    items: {
        topic: string
        subtopics: {
            name: string
            text: string
        }[]
    }[]
}

export type Stage = keyof typeof stages;