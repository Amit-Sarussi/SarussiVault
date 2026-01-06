// Define the hierarchy data structure
export interface HierarchyItem {
	id: string;
	name: string;
	type: 'folder' | 'file';
	children?: HierarchyItem[];
}

