import { WritingCard, ContentChunk, CardboardView, CardPosition, ChunkLayout } from "../types"
import { CardStorage } from "../storage"
import { generateCardId, extractTitle, countWords } from "../utils"

export class CardManager {
	private storage: CardStorage

	constructor(workspaceRoot: string) {
		this.storage = new CardStorage(workspaceRoot)
	}

	async initialize(): Promise<void> {
		await this.storage.initialize()
	}

	// Card CRUD operations
	async createCard(content: string, title?: string, tags: string[] = [], position?: CardPosition): Promise<WritingCard> {
		const id = generateCardId()
		const extractedTitle = title || extractTitle(content)
		const wordCount = countWords(content)

		const card: WritingCard = {
			id,
			title: extractedTitle,
			content,
			tags,
			status: "draft",
			history: [
				{
					timestamp: new Date(),
					content,
					changeType: "create",
				},
			],
			position: position || { x: 0, y: 0, width: 250, height: 200 },
			metadata: {
				wordCount,
				createdAt: new Date(),
				updatedAt: new Date(),
			},
		}

		await this.storage.saveCard(card)
		return card
	}

	async updateCard(id: string, updates: Partial<WritingCard>): Promise<WritingCard> {
		const card = await this.storage.loadCard(id)
		if (!card) {
			throw new Error(`Card with id ${id} not found`)
		}

		const updatedCard: WritingCard = {
			...card,
			...updates,
			metadata: {
				...card.metadata,
				...updates.metadata,
				updatedAt: new Date(),
				wordCount: updates.content ? countWords(updates.content) : card.metadata.wordCount,
			},
		}

		// Add version history entry if content changed
		if (updates.content && updates.content !== card.content) {
			updatedCard.history = [
				...card.history,
				{
					timestamp: new Date(),
					content: updates.content,
					changeType: "edit",
				},
			]
		}

		await this.storage.saveCard(updatedCard)
		return updatedCard
	}

	async deleteCard(id: string): Promise<boolean> {
		return await this.storage.deleteCard(id)
	}

	async getCard(id: string): Promise<WritingCard | null> {
		return await this.storage.loadCard(id)
	}

	async getAllCards(): Promise<WritingCard[]> {
		return await this.storage.loadAllCards()
	}

	async splitCard(id: string, splitPoint: number): Promise<[WritingCard, WritingCard]> {
		const card = await this.storage.loadCard(id)
		if (!card) {
			throw new Error(`Card with id ${id} not found`)
		}

		const content1 = card.content.substring(0, splitPoint).trim()
		const content2 = card.content.substring(splitPoint).trim()

		// Update original card
		const updatedCard1 = await this.updateCard(id, {
			content: content1,
			title: extractTitle(content1),
		})

		// Create new card
		const newCard = await this.createCard(content2, extractTitle(content2), card.tags, {
			x: card.position.x + card.position.width + 20,
			y: card.position.y,
			width: card.position.width,
			height: card.position.height,
		})

		// Add history entries
		updatedCard1.history.push({
			timestamp: new Date(),
			content: content1,
			changeType: "split",
		})

		newCard.history.push({
			timestamp: new Date(),
			content: content2,
			changeType: "split",
		})

		await this.storage.saveCard(updatedCard1)
		await this.storage.saveCard(newCard)

		return [updatedCard1, newCard]
	}

	async mergeCards(id1: string, id2: string): Promise<WritingCard> {
		const card1 = await this.storage.loadCard(id1)
		const card2 = await this.storage.loadCard(id2)

		if (!card1 || !card2) {
			throw new Error("One or both cards not found")
		}

		const mergedContent = `${card1.content}\n\n${card2.content}`
		const mergedTags = [...new Set([...card1.tags, ...card2.tags])]

		const mergedCard = await this.updateCard(id1, {
			content: mergedContent,
			title: extractTitle(mergedContent),
			tags: mergedTags,
		})

		// Add merge history entry
		mergedCard.history.push({
			timestamp: new Date(),
			content: mergedContent,
			changeType: "merge",
		})

		await this.storage.saveCard(mergedCard)
		await this.storage.deleteCard(id2)

		return mergedCard
	}

	// Visual layout operations
	async updateCardPosition(id: string, position: CardPosition): Promise<WritingCard> {
		return await this.updateCard(id, { position })
	}

	async autoArrangeCards(cardIds: string[], layout: ChunkLayout): Promise<WritingCard[]> {
		const cards = await Promise.all(cardIds.map((id) => this.storage.loadCard(id)))
		const validCards = cards.filter((card) => card !== null) as WritingCard[]

		if (layout.type === "grid") {
			const columns = layout.columns || 3
			const spacing = layout.spacing || 20
			const cardWidth = 250
			const cardHeight = 200

			for (let i = 0; i < validCards.length; i++) {
				const row = Math.floor(i / columns)
				const col = i % columns
				const position: CardPosition = {
					x: col * (cardWidth + spacing),
					y: row * (cardHeight + spacing),
					width: cardWidth,
					height: cardHeight,
				}

				validCards[i] = await this.updateCardPosition(validCards[i].id, position)
			}
		} else if (layout.type === "linear") {
			const spacing = layout.spacing || 20
			const cardWidth = 250
			const cardHeight = 200

			for (let i = 0; i < validCards.length; i++) {
				const position: CardPosition = {
					x: i * (cardWidth + spacing),
					y: 0,
					width: cardWidth,
					height: cardHeight,
				}

				validCards[i] = await this.updateCardPosition(validCards[i].id, position)
			}
		}

		return validCards
	}

	// Chunk operations
	async createChunk(
		name: string,
		cardIds: string[] = [],
		purpose: string = "general",
		layout: ChunkLayout = { type: "grid", columns: 3, spacing: 20, autoArrange: true },
	): Promise<ContentChunk> {
		const id = generateCardId()
		const chunk: ContentChunk = {
			id,
			name,
			cardIds,
			purpose,
			layout,
		}

		await this.storage.saveChunk(chunk)

		// Auto-arrange cards if enabled
		if (layout.autoArrange && cardIds.length > 0) {
			await this.autoArrangeCards(cardIds, layout)
		}

		return chunk
	}

	async updateChunk(id: string, updates: Partial<ContentChunk>): Promise<ContentChunk> {
		const chunk = await this.storage.loadChunk(id)
		if (!chunk) {
			throw new Error(`Chunk with id ${id} not found`)
		}

		const updatedChunk: ContentChunk = { ...chunk, ...updates }
		await this.storage.saveChunk(updatedChunk)

		// Auto-arrange if layout changed and auto-arrange is enabled
		if (updates.layout?.autoArrange && updatedChunk.cardIds.length > 0) {
			await this.autoArrangeCards(updatedChunk.cardIds, updatedChunk.layout)
		}

		return updatedChunk
	}

	async deleteChunk(id: string): Promise<boolean> {
		return await this.storage.deleteChunk(id)
	}

	async getChunk(id: string): Promise<ContentChunk | null> {
		return await this.storage.loadChunk(id)
	}

	async getAllChunks(): Promise<ContentChunk[]> {
		return await this.storage.loadAllChunks()
	}

	// Cardboard view operations
	async createView(name: string, description?: string, chunkIds: string[] = []): Promise<CardboardView> {
		const id = generateCardId()
		const view: CardboardView = {
			id,
			name,
			description,
			chunkIds,
			viewSettings: {
				zoom: 1.0,
				centerPoint: { x: 0, y: 0 },
				showMetadata: true,
				showConnections: false,
				groupBy: "none",
			},
		}

		await this.storage.saveView(view)
		return view
	}

	async updateView(id: string, updates: Partial<CardboardView>): Promise<CardboardView> {
		const view = await this.storage.loadView(id)
		if (!view) {
			throw new Error(`View with id ${id} not found`)
		}

		const updatedView: CardboardView = { ...view, ...updates }
		await this.storage.saveView(updatedView)
		return updatedView
	}

	async deleteView(id: string): Promise<boolean> {
		return await this.storage.deleteView(id)
	}

	async getView(id: string): Promise<CardboardView | null> {
		return await this.storage.loadView(id)
	}

	async getAllViews(): Promise<CardboardView[]> {
		return await this.storage.loadAllViews()
	}

	// Utility methods
	async exportChunkAsText(chunkId: string): Promise<string> {
		const chunk = await this.storage.loadChunk(chunkId)
		if (!chunk) {
			throw new Error(`Chunk with id ${chunkId} not found`)
		}

		const cards = await Promise.all(chunk.cardIds.map((id) => this.storage.loadCard(id)))
		const validCards = cards.filter((card) => card !== null) as WritingCard[]

		return validCards.map((card) => card.content).join("\n\n")
	}

	async importTextAsCards(
		text: string,
		chunkName: string,
		splitBy: "paragraph" | "sentence" | "custom" = "paragraph",
	): Promise<ContentChunk> {
		let segments: string[] = []

		if (splitBy === "paragraph") {
			segments = text.split(/\n\s*\n/).filter((s) => s.trim().length > 0)
		} else if (splitBy === "sentence") {
			segments = text.split(/[.!?]+/).filter((s) => s.trim().length > 0)
		} else {
			segments = [text] // Custom logic can be added here
		}

		const cards: WritingCard[] = []
		for (let i = 0; i < segments.length; i++) {
			const content = segments[i].trim()
			const card = await this.createCard(content, extractTitle(content), [], {
				x: (i % 3) * 270,
				y: Math.floor(i / 3) * 220,
				width: 250,
				height: 200,
			})
			cards.push(card)
		}

		const chunk = await this.createChunk(
			chunkName,
			cards.map((c) => c.id),
			"imported-text",
		)

		return chunk
	}
}
