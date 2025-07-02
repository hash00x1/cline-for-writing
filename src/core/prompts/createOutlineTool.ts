import { ToolDefinition } from "@core/prompts/model_prompts/jsonToolToXml"

export const createOutlineToolName = "CreateOutline"

const descriptionForAgent = `Generate an outline from a Markdown, LaTeX or DOCX file by analyzing its headings. The outline is returned as markdown and the file is not modified.`

export const createOutlineToolDefinition: ToolDefinition = {
    name: createOutlineToolName,
    descriptionForAgent,
    inputSchema: {
        type: "object",
        properties: {
            file_path: {
                type: "string",
                description: "Path to the Markdown, LaTeX or DOCX file",
            },
        },
        required: ["file_path"],
    },
}
