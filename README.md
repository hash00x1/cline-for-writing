<div align="center"><sub>
English | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/es/README.md" target="_blank">Español</a> | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/de/README.md" target="_blank">Deutsch</a> | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/ja/README.md" target="_blank">日本語</a> | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/zh-cn/README.md" target="_blank">简体中文</a> | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/zh-tw/README.md" target="_blank">繁體中文</a> | <a href="https://github.com/cline/cline-for-writing/blob/main/locales/ko/README.md" target="_blank">한국어</a>
</sub></div>

# Cline Writer – AI Writing Assistant for Professional Writers

<p align="center">
  <img src="https://media.githubusercontent.com/media/cline/cline-for-writing/main/assets/docs/demo.gif" width="100%" />
</p>

<div align="center">
<table>
<tbody>
<td align="center">
<a href="https://marketplace.visualstudio.com/items?itemName=saoudrizwan.cline-writer" target="_blank"><strong>Download on VS Marketplace</strong></a>
</td>
<td align="center">
<a href="https://discord.gg/cline" target="_blank"><strong>Discord</strong></a>
</td>
<td align="center">
<a href="https://www.reddit.com/r/cline/" target="_blank"><strong>r/cline</strong></a>
</td>
<td align="center">
<a href="https://github.com/cline/cline-for-writing/discussions/categories/feature-requests?discussions_q=is%3Aopen+category%3A%22Feature+Requests%22+sort%3Atop" target="_blank"><strong>Feature Requests</strong></a>
</td>
<td align="center">
<a href="https://docs.cline.bot/getting-started/for-writers" target="_blank"><strong>Getting Started</strong></a>
</td>
</tbody>
</table>
</div>

Meet Cline Writer, an AI assistant designed specifically for professional writers in **academic research**, **screenwriting**, and **novel writing**.

Thanks to [Claude 3.7 Sonnet's advanced reasoning capabilities](https://www.anthropic.com/claude/sonnet), Cline Writer can handle complex writing projects step-by-step. With specialized tools for planning, researching, and drafting, it can assist you in ways that go beyond simple text generation. Cline Writer can even use the Model Context Protocol (MCP) to connect with research databases, citation managers, and other writing tools. The extension provides a human-in-the-loop interface where you approve every outline, research note, and draft, ensuring you remain in complete control of your writing process.

## How Cline Writer Works

1. **Plan**: Tell Cline Writer about your writing project - whether it's a research paper, screenplay, or novel. It can help you create detailed outlines, conduct literature reviews, and organize your project structure.

2. **Research**: Cline Writer analyzes your project goals and existing materials in the `memory_bank` folder to understand your writing context. It can help gather sources, summarize research, and maintain citation databases.

3. **Write**: Once Cline has the information needed, it can:
    - Generate detailed outlines for academic papers, screenplays, or novels
    - Draft chapters, scenes, or sections based on your project state
    - Conduct literature reviews and summarize research findings
    - Manage citations and bibliographies for academic work
    - Develop character arcs and plot structures for creative writing
    - Review and suggest improvements to existing drafts

4. **Iterate**: When a writing task is completed, Cline Writer presents the result in your preferred format, whether it's markdown, LaTeX, or specialized screenplay formats.

## Key Features

- **Academic Writing**: Literature reviews, research organization, citation management, thesis/dissertation support
- **Screenwriting**: Scene planning, character development, dialogue refinement, industry-standard formatting
- **Novel Writing**: Plot development, character arcs, world-building, chapter structuring
- **Project Memory**: Notes on all your outlines, research, and drafts are stored in the `memory_bank` folder for continuity
- **Multiple Formats**: Support for Markdown, LaTeX, Fountain (screenplay), and other writing formats

> [!TIP]
> Use the `CMD/CTRL + Shift + P` shortcut to open the command palette and type "Cline Writer: Open In New Tab" to open the extension as a tab in your editor. This lets you use Cline Writer side-by-side with your documents and project files.

---

<img align="right" width="340" src="https://github.com/user-attachments/assets/3cf21e04-7ce9-4d22-a7b9-ba2c595e88a4">

### Use any AI Model for Writing

Cline Writer supports API providers like Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure, GCP Vertex, and others. You can also configure any OpenAI compatible API, or use a local model through LM Studio/Ollama. The extension fetches the latest model lists, allowing you to use the newest writing-optimized models as soon as they're available.

The extension keeps track of total tokens and API usage cost for your entire writing project, keeping you informed of usage every step of the way.

<!-- Transparent pixel to create line break after floating image -->

<img width="2000" height="0" src="https://github.com/user-attachments/assets/ee14e6f7-20b8-4391-9091-8e8e25561929"><br>

<img align="left" width="370" src="https://github.com/user-attachments/assets/81be79a8-1fdb-4028-9129-5fe055e01e76">

### Plan and Write with Structure

Cline Writer excels at helping you structure your writing projects. Whether you're outlining a research paper, plotting a novel, or planning a screenplay, Cline Writer can help you:

- Create detailed outlines that serve as blueprints for your writing
- Organize research notes and sources in a systematic way
- Track character development and plot progression
- Manage citations and bibliographies automatically
- Maintain consistency across long-form projects

For long writing sessions, use the continuous writing mode to let Cline Writer work on multiple sections while you review and approve each piece.

<!-- Transparent pixel to create line break after floating image -->

<img width="2000" height="0" src="https://github.com/user-attachments/assets/ee14e6f7-20b8-4391-9091-8e8e25561929"><br>

## Writing Modes

### Plan Mode
In Plan mode, Cline Writer helps you structure your project:
- **Academic**: Create research outlines, thesis structures, literature review frameworks
- **Screenwriting**: Develop story beats, character arcs, scene breakdowns
- **Novel**: Plot development, chapter outlines, character profiles, world-building

### Write Mode  
In Write mode, Cline Writer drafts content based on your plans:
- Generate first drafts from outlines
- Expand existing sections with more detail
- Revise and improve existing text
- Maintain consistent style and voice
- Format content for different output types

## Getting Started

1. **Install the extension** from the VS Code Marketplace
2. **Set up your AI provider** (Anthropic Claude recommended for writing tasks)
3. **Create a `memory_bank` folder** in your workspace for project files
4. **Start a new writing project** using the "New Writing Project" command
5. **Choose your writing type**: Academic, Screenwriting, or Novel
6. **Begin planning** your project with Cline Writer's assistance

## Project Structure

Cline Writer organizes your writing projects in the `memory_bank` folder:

```
memory_bank/
├── outlines/           # Project outlines and structures
├── research/           # Research notes and sources
├── drafts/            # Working drafts and revisions
├── characters/        # Character profiles (fiction)
├── citations/         # Bibliography and references
└── project_state.md   # Current project status and goals
```

## Supported Writing Formats

- **Markdown** (.md) - General writing and note-taking
- **LaTeX** (.tex) - Academic papers and theses
- **Fountain** (.fountain) - Screenplay format
- **DOCX** - Microsoft Word documents (via export)
- **PDF** - Final output format (via export)

## Community

Join thousands of writers using Cline Writer:

- [Discord Community](https://discord.gg/cline) - Get help and share your projects
- [Reddit](https://www.reddit.com/r/cline/) - Discussion and tips
- [Documentation](https://docs.cline.bot) - Comprehensive guides and tutorials

## Contributing

Cline Writer is open source! Contribute to making it better for writers worldwide:

- [GitHub Repository](https://github.com/cline/cline-for-writing)
- [Feature Requests](https://github.com/cline/cline-for-writing/discussions/categories/feature-requests)
- [Bug Reports](https://github.com/cline/cline-for-writing/issues)

---

Transform your writing process with AI assistance. Download Cline Writer today and experience the future of professional writing.
