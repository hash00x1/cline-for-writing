import { ToolDefinition } from "@core/prompts/model_prompts/jsonToolToXml"

export const insertCitationToolName = "InsertCitation"

const descriptionForAgent = `Insert a citation into a Markdown or LaTeX document. The citation text is inserted after the first occurrence of the given marker.`

export const insertCitationToolDefinition: ToolDefinition = {
    name: insertCitationToolName,
    descriptionForAgent,
    inputSchema: {
        type: "object",
        properties: {
            file_path: {
                type: "string",
                description: "Path to the Markdown or LaTeX file to modify",
            },
            citation: {
                type: "string",
                description: "Citation text to insert",
            },
            marker: {
                type: "string",
                description: "Marker string in the file after which the citation should be inserted",
            },
        },
        required: ["file_path", "citation", "marker"],
    },
}
