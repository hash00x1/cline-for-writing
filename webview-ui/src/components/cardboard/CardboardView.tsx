import React, { useState, useEffect, useRef, useCallback } from "react"
import { WritingCard, ContentChunk, CardboardView, CardPosition, CardStatus } from "../../types"

interface CardboardProps {
	view: CardboardView
	cards: WritingCard[]
	chunks: ContentChunk[]
	onCardUpdate: (cardId: string, updates: Partial<WritingCard>) => void
	onCardMove: (cardId: string, position: CardPosition) => void
	onCardCreate: (content: string, position: CardPosition) => void
	onCardDelete: (cardId: string) => void
	onViewUpdate: (viewId: string, updates: Partial<CardboardView>) => void
}

interface DragState {
	isDragging: boolean
	draggedCardId: string | null
	offset: { x: number; y: number }
	startPosition: { x: number; y: number }
}

export const Cardboard: React.FC<CardboardProps> = ({
	view,
	cards,
	chunks,
	onCardUpdate,
	onCardMove,
	onCardCreate,
	onCardDelete,
	onViewUpdate,
}) => {
	const [dragState, setDragState] = useState<DragState>({
		isDragging: false,
		draggedCardId: null,
		offset: { x: 0, y: 0 },
		startPosition: { x: 0, y: 0 },
	})

	const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
	const [isCreatingCard, setIsCreatingCard] = useState(false)
	const [newCardPosition, setNewCardPosition] = useState<{ x: number; y: number } | null>(null)
	const [zoom, setZoom] = useState(view.viewSettings.zoom)
	const [panOffset, setPanOffset] = useState(view.viewSettings.centerPoint)

	const canvasRef = useRef<HTMLDivElement>(null)
	const [canvasSize, setCanvasSize] = useState({ width: 2000, height: 2000 })

	// Get cards that are visible in this view
	const visibleCards = cards.filter((card) =>
		view.chunkIds.some((chunkId: string) => chunks.find((chunk) => chunk.id === chunkId)?.cardIds.includes(card.id)),
	)

	// Handle card drag start
	const handleCardMouseDown = useCallback(
		(e: React.MouseEvent, cardId: string) => {
			e.preventDefault()
			e.stopPropagation()

			const card = cards.find((c) => c.id === cardId)
			if (!card) return

			const rect = e.currentTarget.getBoundingClientRect()
			const offset = {
				x: e.clientX - rect.left,
				y: e.clientY - rect.top,
			}

			setDragState({
				isDragging: true,
				draggedCardId: cardId,
				offset,
				startPosition: { x: card.position.x, y: card.position.y },
			})

			setSelectedCardId(cardId)
		},
		[cards],
	)

	// Handle card drag
	const handleMouseMove = useCallback(
		(e: MouseEvent) => {
			if (!dragState.isDragging || !dragState.draggedCardId) return

			const canvas = canvasRef.current
			if (!canvas) return

			const rect = canvas.getBoundingClientRect()
			const x = (e.clientX - rect.left - dragState.offset.x - panOffset.x) / zoom
			const y = (e.clientY - rect.top - dragState.offset.y - panOffset.y) / zoom

			const card = cards.find((c) => c.id === dragState.draggedCardId)
			if (!card) return

			const newPosition: CardPosition = {
				...card.position,
				x: Math.max(0, x),
				y: Math.max(0, y),
			}

			onCardMove(dragState.draggedCardId, newPosition)
		},
		[dragState, cards, zoom, panOffset, onCardMove],
	)

	// Handle card drag end
	const handleMouseUp = useCallback(() => {
		setDragState({
			isDragging: false,
			draggedCardId: null,
			offset: { x: 0, y: 0 },
			startPosition: { x: 0, y: 0 },
		})
	}, [])

	// Handle canvas click for creating new cards
	const handleCanvasClick = useCallback(
		(e: React.MouseEvent) => {
			if (isCreatingCard) {
				const canvas = canvasRef.current
				if (!canvas) return

				const rect = canvas.getBoundingClientRect()
				const x = (e.clientX - rect.left - panOffset.x) / zoom
				const y = (e.clientY - rect.top - panOffset.y) / zoom

				setNewCardPosition({ x, y })
				setIsCreatingCard(false)
			} else {
				setSelectedCardId(null)
			}
		},
		[isCreatingCard, zoom, panOffset],
	)

	// Handle zoom
	const handleWheel = useCallback(
		(e: React.WheelEvent) => {
			e.preventDefault()
			const delta = e.deltaY > 0 ? 0.9 : 1.1
			const newZoom = Math.max(0.1, Math.min(3, zoom * delta))
			setZoom(newZoom)

			onViewUpdate(view.id, {
				viewSettings: {
					...view.viewSettings,
					zoom: newZoom,
				},
			})
		},
		[zoom, view, onViewUpdate],
	)

	// Attach global mouse events for dragging
	useEffect(() => {
		if (dragState.isDragging) {
			document.addEventListener("mousemove", handleMouseMove)
			document.addEventListener("mouseup", handleMouseUp)

			return () => {
				document.removeEventListener("mousemove", handleMouseMove)
				document.removeEventListener("mouseup", handleMouseUp)
			}
		}
	}, [dragState.isDragging, handleMouseMove, handleMouseUp])

	// Create new card
	const createNewCard = useCallback(
		(content: string) => {
			if (newCardPosition) {
				const position: CardPosition = {
					x: newCardPosition.x,
					y: newCardPosition.y,
					width: 250,
					height: 200,
				}
				onCardCreate(content, position)
				setNewCardPosition(null)
			}
		},
		[newCardPosition, onCardCreate],
	)

	return (
		<div className="cardboard-container h-full w-full overflow-hidden bg-gray-50 dark:bg-gray-900 relative">
			{/* Toolbar */}
			<div className="cardboard-toolbar absolute top-0 left-0 right-0 z-10 bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 p-2 flex items-center gap-2">
				<button
					onClick={() => setIsCreatingCard(true)}
					className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
					+ New Card
				</button>

				<div className="flex items-center gap-2 ml-4">
					<label className="text-sm text-gray-600 dark:text-gray-300">Zoom:</label>
					<input
						type="range"
						min="0.1"
						max="3"
						step="0.1"
						value={zoom}
						onChange={(e) => {
							const newZoom = parseFloat(e.target.value)
							setZoom(newZoom)
							onViewUpdate(view.id, {
								viewSettings: { ...view.viewSettings, zoom: newZoom },
							})
						}}
						className="w-20"
					/>
					<span className="text-sm text-gray-600 dark:text-gray-300 w-12">{Math.round(zoom * 100)}%</span>
				</div>

				<div className="flex items-center gap-2 ml-4">
					<label className="text-sm text-gray-600 dark:text-gray-300">
						<input
							type="checkbox"
							checked={view.viewSettings.showMetadata}
							onChange={(e) =>
								onViewUpdate(view.id, {
									viewSettings: { ...view.viewSettings, showMetadata: e.target.checked },
								})
							}
							className="mr-1"
						/>
						Show Metadata
					</label>
				</div>

				<div className="ml-auto text-sm text-gray-600 dark:text-gray-300">
					{visibleCards.length} cards • {view.name}
				</div>
			</div>

			{/* Canvas */}
			<div
				ref={canvasRef}
				className="cardboard-canvas absolute inset-0 top-12 cursor-crosshair"
				style={{
					transform: `scale(${zoom}) translate(${panOffset.x}px, ${panOffset.y}px)`,
					transformOrigin: "0 0",
				}}
				onClick={handleCanvasClick}
				onWheel={handleWheel}>
				{/* Grid background */}
				<svg className="absolute inset-0 pointer-events-none" width={canvasSize.width} height={canvasSize.height}>
					<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
						<path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,0,0,0.1)" strokeWidth="1" />
					</pattern>
					<rect width="100%" height="100%" fill="url(#grid)" />
				</svg>

				{/* Cards */}
				{visibleCards.map((card) => (
					<CardComponent
						key={card.id}
						card={card}
						isSelected={selectedCardId === card.id}
						isDragging={dragState.draggedCardId === card.id}
						showMetadata={view.viewSettings.showMetadata}
						onMouseDown={(e) => handleCardMouseDown(e, card.id)}
						onUpdate={(updates) => onCardUpdate(card.id, updates)}
						onDelete={() => onCardDelete(card.id)}
					/>
				))}

				{/* New card creation overlay */}
				{newCardPosition && (
					<NewCardDialog
						position={newCardPosition}
						onCreateCard={createNewCard}
						onCancel={() => setNewCardPosition(null)}
					/>
				)}
			</div>

			{/* Instructions */}
			{isCreatingCard && (
				<div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-2 rounded shadow-lg">
					Click anywhere on the canvas to create a new card
				</div>
			)}
		</div>
	)
}

// Individual Card Component
interface CardComponentProps {
	card: WritingCard
	isSelected: boolean
	isDragging: boolean
	showMetadata: boolean
	onMouseDown: (e: React.MouseEvent) => void
	onUpdate: (updates: Partial<WritingCard>) => void
	onDelete: () => void
}

const CardComponent: React.FC<CardComponentProps> = ({
	card,
	isSelected,
	isDragging,
	showMetadata,
	onMouseDown,
	onUpdate,
	onDelete,
}) => {
	const [isEditing, setIsEditing] = useState(false)
	const [editContent, setEditContent] = useState(card.content)

	const statusColors: Record<CardStatus, string> = {
		draft: "bg-yellow-100 border-yellow-300 dark:bg-yellow-900 dark:border-yellow-600",
		edited: "bg-blue-100 border-blue-300 dark:bg-blue-900 dark:border-blue-600",
		reviewed: "bg-green-100 border-green-300 dark:bg-green-900 dark:border-green-600",
		final: "bg-purple-100 border-purple-300 dark:bg-purple-900 dark:border-purple-600",
	}

	const handleSave = () => {
		onUpdate({ content: editContent })
		setIsEditing(false)
	}

	const handleCancel = () => {
		setEditContent(card.content)
		setIsEditing(false)
	}

	return (
		<div
			className={`absolute card-component bg-white dark:bg-gray-800 border-2 rounded-lg shadow-lg cursor-move select-none ${
				statusColors[card.status]
			} ${isSelected ? "ring-2 ring-blue-500" : ""} ${isDragging ? "opacity-70 z-50" : "z-10"}`}
			style={{
				left: card.position.x,
				top: card.position.y,
				width: card.position.width,
				height: card.position.height,
			}}
			onMouseDown={onMouseDown}>
			{/* Card Header */}
			<div className="card-header p-2 border-b border-gray-200 dark:border-gray-600 flex items-center justify-between">
				<h3 className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate flex-1">{card.title}</h3>
				<div className="flex items-center gap-1">
					<button
						onClick={(e) => {
							e.stopPropagation()
							setIsEditing(true)
						}}
						className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xs">
						✏️
					</button>
					<button
						onClick={(e) => {
							e.stopPropagation()
							onDelete()
						}}
						className="text-gray-400 hover:text-red-500 text-xs">
						🗑️
					</button>
				</div>
			</div>

			{/* Card Content */}
			<div className="card-content p-2 flex-1 overflow-hidden">
				{isEditing ? (
					<div className="h-full flex flex-col">
						<textarea
							value={editContent}
							onChange={(e) => setEditContent(e.target.value)}
							className="flex-1 w-full resize-none border border-gray-300 dark:border-gray-600 rounded p-1 text-xs bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
							onClick={(e) => e.stopPropagation()}
						/>
						<div className="flex gap-1 mt-1">
							<button
								onClick={handleSave}
								className="px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600">
								Save
							</button>
							<button
								onClick={handleCancel}
								className="px-2 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600">
								Cancel
							</button>
						</div>
					</div>
				) : (
					<div className="text-xs text-gray-700 dark:text-gray-300 overflow-hidden">
						<p className="line-clamp-6">{card.content}</p>
					</div>
				)}
			</div>

			{/* Card Footer (Metadata) */}
			{showMetadata && (
				<div className="card-footer p-2 border-t border-gray-200 dark:border-gray-600 text-xs text-gray-500 dark:text-gray-400">
					<div className="flex justify-between items-center">
						<span>{card.metadata.wordCount} words</span>
						<span className="capitalize">{card.status}</span>
					</div>
					{card.tags.length > 0 && (
						<div className="flex gap-1 mt-1 flex-wrap">
							{card.tags.map((tag: string) => (
								<span key={tag} className="px-1 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-xs">
									{tag}
								</span>
							))}
						</div>
					)}
				</div>
			)}
		</div>
	)
}

// New Card Dialog Component
interface NewCardDialogProps {
	position: { x: number; y: number }
	onCreateCard: (content: string) => void
	onCancel: () => void
}

const NewCardDialog: React.FC<NewCardDialogProps> = ({ position, onCreateCard, onCancel }) => {
	const [content, setContent] = useState("")

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		if (content.trim()) {
			onCreateCard(content.trim())
		}
	}

	return (
		<div
			className="absolute bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-xl p-4 z-50"
			style={{
				left: position.x,
				top: position.y,
				width: 300,
			}}>
			<form onSubmit={handleSubmit}>
				<h3 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Create New Card</h3>
				<textarea
					value={content}
					onChange={(e) => setContent(e.target.value)}
					placeholder="Enter card content..."
					className="w-full h-24 border border-gray-300 dark:border-gray-600 rounded p-2 text-sm bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 resize-none"
					autoFocus
				/>
				<div className="flex gap-2 mt-2">
					<button type="submit" className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">
						Create
					</button>
					<button
						type="button"
						onClick={onCancel}
						className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600">
						Cancel
					</button>
				</div>
			</form>
		</div>
	)
}
