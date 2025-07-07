export interface WritingCard {
	id: string
	title: string
	content: string
	tags: string[]
	status: CardStatus
	history: VersionEntry[]
	position: CardPosition
	metadata: {
		wordCount: number
		createdAt: Date
		updatedAt: Date
		chunkId?: string
		color?: string
		priority?: number
	}
}

export interface VersionEntry {
	timestamp: Date
	content: string
	author?: string
	changeType: "create" | "edit" | "merge" | "split"
}

export interface ContentChunk {
	id: string
	name: string
	cardIds: string[]
	purpose: string
	layout: ChunkLayout
}

export interface CardPosition {
	x: number
	y: number
	width: number
	height: number
	zIndex?: number
}

export interface ChunkLayout {
	type: "grid" | "freeform" | "linear"
	columns?: number
	spacing?: number
	autoArrange?: boolean
}

export type CardStatus = "draft" | "edited" | "reviewed" | "final"

export interface CardboardView {
	id: string
	name: string
	description?: string
	chunkIds: string[]
	viewSettings: {
		zoom: number
		centerPoint: { x: number; y: number }
		showMetadata: boolean
		showConnections: boolean
		groupBy?: "status" | "tags" | "chunk" | "none"
	}
}
