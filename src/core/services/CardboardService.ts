import { CardManager } from "./CardManager"
import { WritingCard, ContentChunk, CardboardView, CardPosition } from "../../types/WritingCard"
import * as vscode from "vscode"

export class CardboardService {
	private cardManagerMap: Map<string, CardManager> = new Map()

	async getCardManager(workspaceRoot: string): Promise<CardManager> {
		if (!this.cardManagerMap.has(workspaceRoot)) {
			const cardManager = new CardManager(workspaceRoot)
			await cardManager.initialize()
			this.cardManagerMap.set(workspaceRoot, cardManager)
		}
		return this.cardManagerMap.get(workspaceRoot)!
	}

	async initializeCardboard(workspaceRoot: string): Promise<{
		cards: WritingCard[]
		chunks: ContentChunk[]
		views: CardboardView[]
	}> {
		const cardManager = await this.getCardManager(workspaceRoot)

		const [cards, chunks, views] = await Promise.all([
			cardManager.getAllCards(),
			cardManager.getAllChunks(),
			cardManager.getAllViews(),
		])

		return { cards, chunks, views }
	}

	async createCard(
		workspaceRoot: string,
		content: string,
		position: CardPosition,
		title?: string,
		tags?: string[],
	): Promise<WritingCard> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.createCard(content, title, tags, position)
	}

	async updateCard(workspaceRoot: string, cardId: string, updates: Partial<WritingCard>): Promise<WritingCard> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.updateCard(cardId, updates)
	}

	async deleteCard(workspaceRoot: string, cardId: string): Promise<boolean> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.deleteCard(cardId)
	}

	async createChunk(
		workspaceRoot: string,
		name: string,
		cardIds: string[] = [],
		purpose: string = "general",
	): Promise<ContentChunk> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.createChunk(name, cardIds, purpose)
	}

	async updateChunk(workspaceRoot: string, chunkId: string, updates: Partial<ContentChunk>): Promise<ContentChunk> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.updateChunk(chunkId, updates)
	}

	async deleteChunk(workspaceRoot: string, chunkId: string): Promise<boolean> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.deleteChunk(chunkId)
	}

	async createView(workspaceRoot: string, name: string, description?: string, chunkIds: string[] = []): Promise<CardboardView> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.createView(name, description, chunkIds)
	}

	async updateView(workspaceRoot: string, viewId: string, updates: Partial<CardboardView>): Promise<CardboardView> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.updateView(viewId, updates)
	}

	async deleteView(workspaceRoot: string, viewId: string): Promise<boolean> {
		const cardManager = await this.getCardManager(workspaceRoot)
		return await cardManager.deleteView(viewId)
	}

	async importTextAsCards(
		workspaceRoot: string,
		text: string,
		chunkName: string,
	): Promise<{ chunk: ContentChunk; cards: WritingCard[] }> {
		const cardManager = await this.getCardManager(workspaceRoot)
		const chunk = await cardManager.importTextAsCards(text, chunkName)

		// Get the created cards
		const cards = await Promise.all(chunk.cardIds.map((id) => cardManager.getCard(id)))

		return {
			chunk,
			cards: cards.filter((card) => card !== null) as WritingCard[],
		}
	}

	async exportViewAsText(workspaceRoot: string, viewId: string): Promise<string> {
		const cardManager = await this.getCardManager(workspaceRoot)
		const view = await cardManager.getView(viewId)

		if (!view) {
			throw new Error(`View with id ${viewId} not found`)
		}

		// Get all chunks in the view and export as text
		let exportText = ""
		for (const chunkId of view.chunkIds) {
			const chunkText = await cardManager.exportChunkAsText(chunkId)
			exportText += chunkText + "\n\n"
		}

		return exportText.trim()
	}

	async createDocumentFromText(text: string, language: string = "markdown"): Promise<void> {
		const document = await vscode.workspace.openTextDocument({
			content: text,
			language: language,
		})

		await vscode.window.showTextDocument(document)
	}

	dispose(): void {
		this.cardManagerMap.clear()
	}
}
