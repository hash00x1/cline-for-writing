import React, { useState, useEffect } from "react"
import { Cardboard } from "./CardboardView"
import { WritingCard, ContentChunk, CardboardView, CardPosition } from "../../types"
import { vscode } from "../../utils/vscode"

interface CardboardManagerProps {
	workspaceRoot?: string
	onDone?: () => void
}

export const CardboardManager: React.FC<CardboardManagerProps> = ({ workspaceRoot, onDone }) => {
	const [cards, setCards] = useState<WritingCard[]>([])
	const [chunks, setChunks] = useState<ContentChunk[]>([])
	const [views, setViews] = useState<CardboardView[]>([])
	const [currentView, setCurrentView] = useState<CardboardView | null>(null)
	const [isLoading, setIsLoading] = useState(true)

	// Listen for messages from the backend
	useEffect(() => {
		const handleMessage = (event: MessageEvent) => {
			const message = event.data

			switch (message.type) {
				case "cardCreated":
					if (message.card) {
						setCards((prev) => [...prev, message.card])
					}
					break
				case "cardUpdated":
					if (message.card) {
						setCards((prev) => prev.map((card) => (card.id === message.card.id ? message.card : card)))
					}
					break
				case "cardDeleted":
					if (message.cardId) {
						setCards((prev) => prev.filter((card) => card.id !== message.cardId))
					}
					break
				case "chunkCreated":
					if (message.chunk) {
						setChunks((prev) => [...prev, message.chunk])
					}
					break
				case "viewCreated":
					if (message.view) {
						setViews((prev) => [...prev, message.view])
					}
					break
			}
		}

		window.addEventListener("message", handleMessage)
		return () => window.removeEventListener("message", handleMessage)
	}, [])

	// Initialize the cardboard system
	useEffect(() => {
		initializeCardboard()
	}, [])

	const initializeCardboard = async () => {
		try {
			console.log("[DEBUG] Initializing cardboard...")
			// Send request to initialize cardboard
			vscode.postMessage({
				type: "initializeCardboard",
			})

			// Create default view
			const defaultView: CardboardView = {
				id: "default-view",
				name: "Main Board",
				description: "Main cardboard view",
				chunkIds: [],
				viewSettings: {
					zoom: 1.0,
					centerPoint: { x: 0, y: 0 },
					showMetadata: true,
					showConnections: false,
					groupBy: "none",
				},
			}

			console.log("[DEBUG] Setting default view:", defaultView)
			setViews([defaultView])
			setCurrentView(defaultView)

			// Create a test card to verify the cardboard is working
			const testCard: WritingCard = {
				id: "test-card-1",
				title: "Test Card",
				content: "This is a test card to verify the cardboard is working correctly.",
				tags: ["test"],
				status: "draft",
				history: [
					{
						timestamp: new Date(),
						content: "This is a test card to verify the cardboard is working correctly.",
						changeType: "create",
					},
				],
				position: {
					x: 100,
					y: 100,
					width: 250,
					height: 200,
				},
				metadata: {
					wordCount: 12,
					createdAt: new Date(),
					updatedAt: new Date(),
				},
			}

			// Create a test chunk that includes the test card
			const testChunk: ContentChunk = {
				id: "test-chunk-1",
				name: "Test Chunk",
				cardIds: [testCard.id],
				purpose: "testing",
				layout: {
					type: "freeform",
					autoArrange: false,
				},
			}

			// Update the default view to include the test chunk
			const viewWithTestData = {
				...defaultView,
				chunkIds: [testChunk.id],
			}

			console.log("[DEBUG] Adding test data - card:", testCard)
			console.log("[DEBUG] Adding test data - chunk:", testChunk)
			setCards([testCard])
			setChunks([testChunk])
			setViews([viewWithTestData])
			setCurrentView(viewWithTestData)
		} catch (error) {
			console.error("Failed to initialize cardboard:", error)
		} finally {
			setIsLoading(false)
		}
	}

	const createView = (name: string, description?: string): CardboardView => {
		const newView: CardboardView = {
			id: `view-${Date.now()}`,
			name,
			description,
			chunkIds: [],
			viewSettings: {
				zoom: 1.0,
				centerPoint: { x: 0, y: 0 },
				showMetadata: true,
				showConnections: false,
				groupBy: "none",
			},
		}

		vscode.postMessage({
			type: "createView",
			view: newView,
		})

		setViews((prev) => [...prev, newView])
		return newView
	}

	const handleCardUpdate = (cardId: string, updates: Partial<WritingCard>) => {
		vscode.postMessage({
			type: "updateCard",
			cardId,
			updates,
		})
	}

	const handleCardMove = (cardId: string, position: CardPosition) => {
		handleCardUpdate(cardId, { position })
	}

	const handleCardCreate = (content: string, position: CardPosition) => {
		const newCard: WritingCard = {
			id: `card-${Date.now()}`,
			title: content.split("\n")[0].substring(0, 50) || "Untitled Card",
			content,
			tags: [],
			status: "draft",
			history: [
				{
					timestamp: new Date(),
					content,
					changeType: "create",
				},
			],
			position,
			metadata: {
				wordCount: content.split(/\s+/).length,
				createdAt: new Date(),
				updatedAt: new Date(),
			},
		}

		vscode.postMessage({
			type: "createCard",
			card: newCard,
		})
	}

	const handleCardDelete = (cardId: string) => {
		vscode.postMessage({
			type: "deleteCard",
			cardId,
		})
	}

	const handleViewUpdate = (viewId: string, updates: Partial<CardboardView>) => {
		vscode.postMessage({
			type: "updateView",
			viewId,
			updates,
		})

		setViews((prev) => prev.map((view) => (view.id === viewId ? { ...view, ...updates } : view)))

		if (currentView && currentView.id === viewId) {
			setCurrentView((prev) => (prev ? { ...prev, ...updates } : null))
		}
	}

	const handleImportText = (text: string, chunkName: string) => {
		const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim().length > 0)

		const newCards: WritingCard[] = paragraphs.map((content, index) => ({
			id: `card-${Date.now()}-${index}`,
			title: content.split("\n")[0].substring(0, 50) || "Untitled Card",
			content: content.trim(),
			tags: ["imported"],
			status: "draft" as const,
			history: [
				{
					timestamp: new Date(),
					content: content.trim(),
					changeType: "create" as const,
				},
			],
			position: {
				x: (index % 3) * 270,
				y: Math.floor(index / 3) * 220,
				width: 250,
				height: 200,
			},
			metadata: {
				wordCount: content.trim().split(/\s+/).length,
				createdAt: new Date(),
				updatedAt: new Date(),
			},
		}))

		const newChunk: ContentChunk = {
			id: `chunk-${Date.now()}`,
			name: chunkName,
			cardIds: newCards.map((c) => c.id),
			purpose: "imported-text",
			layout: {
				type: "grid",
				columns: 3,
				spacing: 20,
				autoArrange: true,
			},
		}

		vscode.postMessage({
			type: "importTextAsCards",
			text,
			chunkName,
			cards: newCards,
			chunk: newChunk,
		})

		// Update local state immediately for better UX
		setCards((prev) => [...prev, ...newCards])
		setChunks((prev) => [...prev, newChunk])

		if (currentView) {
			const updatedView = {
				...currentView,
				chunkIds: [...currentView.chunkIds, newChunk.id],
			}
			setCurrentView(updatedView)
			setViews((prev) => prev.map((view) => (view.id === currentView.id ? updatedView : view)))
		}
	}

	const handleExportView = () => {
		if (!currentView) return

		const viewCards = cards.filter((card) =>
			currentView.chunkIds.some((chunkId) => chunks.find((chunk) => chunk.id === chunkId)?.cardIds.includes(card.id)),
		)

		const exportText = viewCards
			.sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x)
			.map((card) => card.content)
			.join("\n\n")

		vscode.postMessage({
			type: "exportViewAsText",
			viewId: currentView.id,
			text: exportText,
		})
	}

	if (isLoading) {
		return (
			<div className="flex items-center justify-center h-full">
				<div className="text-gray-600 dark:text-gray-300">Loading cardboard...</div>
			</div>
		)
	}

	if (!currentView) {
		return (
			<div className="flex items-center justify-center h-full">
				<div className="text-center">
					<div className="text-gray-600 dark:text-gray-300 mb-4">No cardboard view available</div>
					<button
						onClick={() => {
							const view = createView("Main Board")
							setCurrentView(view)
						}}
						className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
						Create Main Board
					</button>
				</div>
			</div>
		)
	}

	return (
		<div className="cardboard-manager h-full flex flex-col">
			{/* View Selector and Actions */}
			<div className="cardboard-header bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-3 flex items-center justify-between">
				<div className="flex items-center gap-4">
					{onDone && (
						<button onClick={onDone} className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600">
							← Back to Chat
						</button>
					)}
					<select
						value={currentView.id}
						onChange={(e) => {
							const view = views.find((v) => v.id === e.target.value)
							if (view) setCurrentView(view)
						}}
						className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200">
						{views.map((view) => (
							<option key={view.id} value={view.id}>
								{view.name}
							</option>
						))}
					</select>

					<button
						onClick={() => {
							const view = createView(`Board ${views.length + 1}`)
							setCurrentView(view)
						}}
						className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600">
						+ New Board
					</button>
				</div>

				<div className="flex items-center gap-2">
					<button
						onClick={() => {
							const text = prompt("Enter text to import as cards:")
							if (text) {
								const chunkName = prompt("Enter chunk name:", "Imported Text") || "Imported Text"
								handleImportText(text, chunkName)
							}
						}}
						className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">
						Import Text
					</button>

					<button
						onClick={handleExportView}
						className="px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600">
						Export as Text
					</button>
				</div>
			</div>

			{/* Cardboard View */}
			<div className="flex-1">
				<Cardboard
					view={currentView}
					cards={cards}
					chunks={chunks}
					onCardUpdate={handleCardUpdate}
					onCardMove={handleCardMove}
					onCardCreate={handleCardCreate}
					onCardDelete={handleCardDelete}
					onViewUpdate={handleViewUpdate}
				/>
			</div>
		</div>
	)
}
