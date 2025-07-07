import * as path from "path"
import * as fs from "fs/promises"
import { WritingCard, ContentChunk, CardboardView } from "../types"

export class CardStorage {
	private storageDir: string
	private cardsDir: string
	private chunksDir: string
	private viewsDir: string

	constructor(workspaceRoot: string) {
		this.storageDir = path.join(workspaceRoot, ".cline-writing")
		this.cardsDir = path.join(this.storageDir, "cards")
		this.chunksDir = path.join(this.storageDir, "chunks")
		this.viewsDir = path.join(this.storageDir, "views")
	}

	async initialize(): Promise<void> {
		await this.ensureDirectories()
	}

	private async ensureDirectories(): Promise<void> {
		await fs.mkdir(this.storageDir, { recursive: true })
		await fs.mkdir(this.cardsDir, { recursive: true })
		await fs.mkdir(this.chunksDir, { recursive: true })
		await fs.mkdir(this.viewsDir, { recursive: true })
	}

	// Card operations
	async saveCard(card: WritingCard): Promise<void> {
		const filePath = path.join(this.cardsDir, `${card.id}.json`)
		const data = JSON.stringify(card, null, 2)
		await fs.writeFile(filePath, data, "utf8")
	}

	async loadCard(id: string): Promise<WritingCard | null> {
		try {
			const filePath = path.join(this.cardsDir, `${id}.json`)
			const data = await fs.readFile(filePath, "utf8")
			return JSON.parse(data) as WritingCard
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return null
			}
			throw error
		}
	}

	async loadAllCards(): Promise<WritingCard[]> {
		try {
			const files = await fs.readdir(this.cardsDir)
			const cardFiles = files.filter((file) => file.endsWith(".json"))

			const cards: WritingCard[] = []
			for (const file of cardFiles) {
				const id = path.basename(file, ".json")
				const card = await this.loadCard(id)
				if (card) {
					cards.push(card)
				}
			}

			return cards
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return []
			}
			throw error
		}
	}

	async deleteCard(id: string): Promise<boolean> {
		try {
			const filePath = path.join(this.cardsDir, `${id}.json`)
			await fs.unlink(filePath)
			return true
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return false
			}
			throw error
		}
	}

	// Chunk operations
	async saveChunk(chunk: ContentChunk): Promise<void> {
		const filePath = path.join(this.chunksDir, `${chunk.id}.json`)
		const data = JSON.stringify(chunk, null, 2)
		await fs.writeFile(filePath, data, "utf8")
	}

	async loadChunk(id: string): Promise<ContentChunk | null> {
		try {
			const filePath = path.join(this.chunksDir, `${id}.json`)
			const data = await fs.readFile(filePath, "utf8")
			return JSON.parse(data) as ContentChunk
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return null
			}
			throw error
		}
	}

	async loadAllChunks(): Promise<ContentChunk[]> {
		try {
			const files = await fs.readdir(this.chunksDir)
			const chunkFiles = files.filter((file) => file.endsWith(".json"))

			const chunks: ContentChunk[] = []
			for (const file of chunkFiles) {
				const id = path.basename(file, ".json")
				const chunk = await this.loadChunk(id)
				if (chunk) {
					chunks.push(chunk)
				}
			}

			return chunks
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return []
			}
			throw error
		}
	}

	async deleteChunk(id: string): Promise<boolean> {
		try {
			const filePath = path.join(this.chunksDir, `${id}.json`)
			await fs.unlink(filePath)
			return true
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return false
			}
			throw error
		}
	}

	// Cardboard view operations
	async saveView(view: CardboardView): Promise<void> {
		const filePath = path.join(this.viewsDir, `${view.id}.json`)
		const data = JSON.stringify(view, null, 2)
		await fs.writeFile(filePath, data, "utf8")
	}

	async loadView(id: string): Promise<CardboardView | null> {
		try {
			const filePath = path.join(this.viewsDir, `${id}.json`)
			const data = await fs.readFile(filePath, "utf8")
			return JSON.parse(data) as CardboardView
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return null
			}
			throw error
		}
	}

	async loadAllViews(): Promise<CardboardView[]> {
		try {
			const files = await fs.readdir(this.viewsDir)
			const viewFiles = files.filter((file) => file.endsWith(".json"))

			const views: CardboardView[] = []
			for (const file of viewFiles) {
				const id = path.basename(file, ".json")
				const view = await this.loadView(id)
				if (view) {
					views.push(view)
				}
			}

			return views
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return []
			}
			throw error
		}
	}

	async deleteView(id: string): Promise<boolean> {
		try {
			const filePath = path.join(this.viewsDir, `${id}.json`)
			await fs.unlink(filePath)
			return true
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code === "ENOENT") {
				return false
			}
			throw error
		}
	}
}
