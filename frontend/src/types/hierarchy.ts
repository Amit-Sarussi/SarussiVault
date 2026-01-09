// Define the hierarchy data structure
export interface HierarchyItem {
	id: string;
	name: string;
	path: string;
	type: 'folder' | 'file';
	children?: HierarchyItem[];
}

