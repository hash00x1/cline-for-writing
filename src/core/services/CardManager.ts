import {
	WritingCard,
	CardStatus,
	VersionEntry,
	CardPosition,
	ContentChunk,
	CardboardView,
	ChunkLayout,
} from "../../types/WritingCard"
import * as fs from "fs"
import * as path from "path"

export class CardManager {
	private cards: Map<string, WritingCard> = new Map()
	private chunks: Map<string, ContentChunk> = new Map()
	private views: Map<string, CardboardView> = new Map()
	private nextId = 1
	private workspaceRoot: string

	constructor(workspaceRoot: string) {
		this.workspaceRoot = workspaceRoot
	}

	async initialize(): Promise<void> {
		// Load existing data from workspace if available
		await this.loadFromWorkspace()
	}

	createCard(content: string, title?: string, tags: string[] = [], position?: CardPosition): WritingCard {
		const id = this.generateId()
		const now = new Date()
		const finalTitle = title || `Card ${this.nextId}`
		const finalPosition = position || { x: 0, y: 0, width: 200, height: 150 }

		const card: WritingCard = {
			id,
			title: finalTitle,
			content,
			tags,
			status: "draft" as CardStatus,
			history: [
				{
					timestamp: now,
					content,
					changeType: "create",
				},
			],
			position: finalPosition,
			metadata: {
				wordCount: this.countWords(content),
				createdAt: now,
				updatedAt: now,
			},
		}

		this.cards.set(id, card)
		return card
	}

	getCard(id: string): WritingCard | null {
		return this.cards.get(id) || null
	}

	getAllCards(): WritingCard[] {
		return Array.from(this.cards.values())
	}

	updateCard(id: string, updates: Partial<WritingCard>): WritingCard {
		const card = this.cards.get(id)
		if (!card) {
			throw new Error(`Card with id ${id} not found`)
		}

		const now = new Date()
		const updatedCard = { ...card, ...updates }

		// Update metadata
		updatedCard.metadata = {
			...card.metadata,
			...updates.metadata,
			updatedAt: now,
		}

		// If content changed, add to history
		if (updates.content && updates.content !== card.content) {
			updatedCard.history = [
				...card.history,
				{
					timestamp: now,
					content: updates.content,
					changeType: "edit",
				},
			]
			updatedCard.metadata.wordCount = this.countWords(updates.content)
		}

		this.cards.set(id, updatedCard)
		return updatedCard
	}

	deleteCard(id: string): boolean {
		return this.cards.delete(id)
	}

	updatePosition(id: string, position: CardPosition): WritingCard {
		const card = this.cards.get(id)
		if (!card) {
			throw new Error(`Card with id ${id} not found`)
		}

		const updatedCard = {
			...card,
			position,
			metadata: {
				...card.metadata,
				updatedAt: new Date(),
			},
		}

		this.cards.set(id, updatedCard)
		return updatedCard
	}

	getAllChunks(): ContentChunk[] {
		return Array.from(this.chunks.values())
	}

	getAllViews(): CardboardView[] {
		return Array.from(this.views.values())
	}

	createChunk(name: string, cardIds: string[] = [], purpose: string = "general"): ContentChunk {
		const id = this.generateId()
		const chunk: ContentChunk = {
			id,
			name,
			cardIds,
			purpose,
			layout: {
				type: "grid",
				columns: 3,
				spacing: 10,
				autoArrange: true,
			},
		}

		this.chunks.set(id, chunk)
		return chunk
	}

	updateChunk(chunkId: string, updates: Partial<ContentChunk>): ContentChunk {
		const chunk = this.chunks.get(chunkId)
		if (!chunk) {
			throw new Error(`Chunk with id ${chunkId} not found`)
		}

		const updatedChunk = { ...chunk, ...updates }
		this.chunks.set(chunkId, updatedChunk)
		return updatedChunk
	}

	deleteChunk(chunkId: string): boolean {
		return this.chunks.delete(chunkId)
	}

	createView(name: string, description: string = "", chunkIds: string[] = []): CardboardView {
		const id = this.generateId()
		const view: CardboardView = {
			id,
			name,
			description,
			chunkIds,
			viewSettings: {
				zoom: 1,
				centerPoint: { x: 0, y: 0 },
				showMetadata: true,
				showConnections: false,
				groupBy: "none",
			},
		}

		this.views.set(id, view)
		return view
	}

	updateView(viewId: string, updates: Partial<CardboardView>): CardboardView {
		const view = this.views.get(viewId)
		if (!view) {
			throw new Error(`View with id ${viewId} not found`)
		}

		const updatedView = { ...view, ...updates }
		this.views.set(viewId, updatedView)
		return updatedView
	}

	deleteView(viewId: string): boolean {
		return this.views.delete(viewId)
	}

	getView(viewId: string): CardboardView | null {
		return this.views.get(viewId) || null
	}

	importTextAsCards(text: string, chunkName: string): ContentChunk {
		// Split text into paragraphs and create cards
		const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim().length > 0)
		const cardIds: string[] = []

		paragraphs.forEach((paragraph, index) => {
			const card = this.createCard(paragraph.trim(), `${chunkName} - Part ${index + 1}`, [chunkName, "imported"])
			cardIds.push(card.id)
		})

		return this.createChunk(chunkName, cardIds, "imported-text")
	}

	exportChunkAsText(chunkId: string): string {
		const chunk = this.chunks.get(chunkId)
		if (!chunk) return ""

		const cards = chunk.cardIds.map((id) => this.getCard(id)).filter((card) => card !== null) as WritingCard[]

		return cards.map((card) => card.content).join("\n\n")
	}

	private generateId(): string {
		return `card_${this.nextId++}_${Date.now()}`
	}

	private countWords(text: string): number {
		return text
			.trim()
			.split(/\s+/)
			.filter((word) => word.length > 0).length
	}

	private async loadFromWorkspace(): Promise<void> {
		// This would load saved cardboard data from the workspace
		// For now, just initialize empty collections
		const dataPath = path.join(this.workspaceRoot, ".cline", "cardboard.json")

		try {
			if (fs.existsSync(dataPath)) {
				const data = JSON.parse(fs.readFileSync(dataPath, "utf8"))
				// Load cards, chunks, views from saved data
				if (data.cards) {
					this.cards = new Map(Object.entries(data.cards))
				}
				if (data.chunks) {
					this.chunks = new Map(Object.entries(data.chunks))
				}
				if (data.views) {
					this.views = new Map(Object.entries(data.views))
				}
				this.nextId = data.nextId || 1
			}
		} catch (error) {
			console.warn("Failed to load cardboard data:", error)
		}
	}

	async saveToWorkspace(): Promise<void> {
		const dataPath = path.join(this.workspaceRoot, ".cline", "cardboard.json")
		const dataDir = path.dirname(dataPath)

		try {
			if (!fs.existsSync(dataDir)) {
				fs.mkdirSync(dataDir, { recursive: true })
			}

			const data = {
				cards: Object.fromEntries(this.cards),
				chunks: Object.fromEntries(this.chunks),
				views: Object.fromEntries(this.views),
				nextId: this.nextId,
			}

			fs.writeFileSync(dataPath, JSON.stringify(data, null, 2))
		} catch (error) {
			console.error("Failed to save cardboard data:", error)
		}
	}
}
