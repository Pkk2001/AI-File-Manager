import React, { useState, useEffect } from 'react';
import type { FileResultItem, SearchMode } from '../types';
import { 
  FileText, 
  Image as ImageIcon, 
  Film, 
  Music, 
  Archive, 
  Code, 
  Cpu, 
  FolderOpen, 
  ExternalLink, 
  Grid, 
  List, 
  Sparkles 
} from 'lucide-react';

interface SearchResultsViewProps {
  results: FileResultItem[];
  searchMode: SearchMode;
  onOpenPath: (path: string) => void;
  onOpenFolder: (path: string) => void;
  isLoading: boolean;
}

export const SearchResultsView: React.FC<SearchResultsViewProps> = ({
  results,
  searchMode,
  onOpenPath,
  onOpenFolder,
  isLoading
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [viewStyle, setViewStyle] = useState<'table' | 'grid'>(searchMode === 'image' ? 'grid' : 'table');

  useEffect(() => {
    if (searchMode === 'image') {
      setViewStyle('grid');
    }
  }, [searchMode]);

  const [loadingText, setLoadingText] = useState<string>('Executing AI query across indexed database...');

  useEffect(() => {
    if (isLoading) {
      setLoadingText('Executing AI query across indexed database...');
      const timer = setTimeout(() => {
        setLoadingText('Loading Vision Model & Calculating Cosine Similarities...');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  const categories = ['All', 'Documents', 'Images', 'Videos', 'Audio', 'Archives', 'Source Code', 'Executable/Apps', 'Other'];

  const filteredResults = selectedCategory === 'All'
    ? results
    : results.filter(r => r.category === selectedCategory);

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'Documents': return <FileText className="w-4 h-4 text-blue-600" />;
      case 'Images': return <ImageIcon className="w-4 h-4 text-emerald-600" />;
      case 'Videos': return <Film className="w-4 h-4 text-purple-600" />;
      case 'Audio': return <Music className="w-4 h-4 text-pink-600" />;
      case 'Archives': return <Archive className="w-4 h-4 text-amber-600" />;
      case 'Source Code': return <Code className="w-4 h-4 text-teal-600" />;
      case 'Executable/Apps': return <Cpu className="w-4 h-4 text-red-600" />;
      default: return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-brand-cream overflow-hidden">
      {/* Category Filter Bar & View Toggle */}
      <div className="bg-white border-b border-brand-sage/20 px-4 py-2 flex items-center justify-between shadow-sm">
        {/* Category Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto py-0.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-brand-darkGreen text-white shadow'
                  : 'bg-gray-100 text-brand-charcoal hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* View Style Selector */}
        <div className="flex items-center space-x-1 border border-brand-sage/30 p-0.5 rounded bg-gray-50 ml-2">
          <button
            onClick={() => setViewStyle('table')}
            className={`p-1 rounded transition-colors ${
              viewStyle === 'table' ? 'bg-brand-sage text-white' : 'text-gray-500 hover:text-brand-charcoal'
            }`}
            title="List / Table View"
          >
            <List className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setViewStyle('grid')}
            className={`p-1 rounded transition-colors ${
              viewStyle === 'grid' ? 'bg-brand-sage text-white' : 'text-gray-500 hover:text-brand-charcoal'
            }`}
            title="Gallery / Grid View"
          >
            <Grid className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Results Body */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3 text-brand-sage">
            <Sparkles className="w-8 h-8 animate-spin" />
            <p className="text-sm font-semibold">{loadingText}</p>
          </div>
        ) : filteredResults.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-2 text-gray-500">
            <FileText className="w-10 h-10 text-gray-400" />
            <p className="text-sm font-medium">No matching images found or search error</p>
            <p className="text-xs text-gray-400">Try searching for a different prompt or image description</p>
          </div>
        ) : viewStyle === 'table' ? (
          /* Table View */
          <div className="bg-white rounded-xl border border-brand-sage/20 shadow-sm overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-brand-darkGreen text-white font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-3 py-2.5">File Name</th>
                  <th className="px-3 py-2.5">Category</th>
                  <th className="px-3 py-2.5">Size</th>
                  <th className="px-3 py-2.5">Match Score</th>
                  <th className="px-3 py-2.5">Full Path</th>
                  <th className="px-3 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono">
                {filteredResults.map((item, idx) => (
                  <tr 
                    key={idx} 
                    className="hover:bg-brand-cream/60 transition-colors group cursor-pointer"
                    onDoubleClick={() => onOpenPath(item.path)}
                  >
                    <td className="px-3 py-2 font-medium text-brand-darkGreen truncate max-w-xs flex items-center space-x-2">
                      {getCategoryIcon(item.category)}
                      <span className="truncate font-sans font-semibold">{item.name}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-600 font-sans">{item.category}</td>
                    <td className="px-3 py-2 text-gray-700">{item.formatted_size}</td>
                    <td className="px-3 py-2 font-sans">
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                        {item.score}% match
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-500 truncate max-w-sm text-[11px]" title={item.path}>
                      {item.path}
                    </td>
                    <td className="px-3 py-2 text-right space-x-1 font-sans">
                      <button
                        onClick={() => onOpenPath(item.path)}
                        className="p-1 rounded text-brand-sage hover:bg-brand-sage hover:text-white transition-colors"
                        title="Open File"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onOpenFolder(item.path)}
                        className="p-1 rounded text-amber-600 hover:bg-amber-600 hover:text-white transition-colors"
                        title="Show in Folder"
                      >
                        <FolderOpen className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Card / Grid View */
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredResults.map((item, idx) => (
              <div 
                key={idx}
                className="bg-white rounded-xl border border-brand-sage/20 p-3 shadow-sm hover:shadow-md hover:border-brand-sage/50 transition-all flex flex-col justify-between space-y-3 cursor-pointer group"
                onDoubleClick={() => onOpenPath(item.path)}
              >
                <div className="space-y-2">
                  <div className="h-28 bg-brand-cream/80 rounded-lg flex items-center justify-center border border-dashed border-brand-sage/20 overflow-hidden relative">
                    {getCategoryIcon(item.category)}
                    <span className="absolute top-2 right-2 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm font-sans">
                      {item.score}% Match
                    </span>
                  </div>

                  <div className="space-y-0.5">
                    <h3 className="text-xs font-bold text-brand-darkGreen truncate" title={item.name}>
                      {item.name}
                    </h3>
                    <p className="text-[11px] text-gray-500 font-mono">{item.formatted_size} • {item.extension}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-xs">
                  <span className="text-[10px] text-gray-400 truncate max-w-[130px]" title={item.path}>
                    {item.path}
                  </span>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => onOpenPath(item.path)}
                      className="flex items-center space-x-1 px-2 py-0.5 bg-brand-sage text-white text-[11px] font-semibold rounded hover:bg-emerald-600 transition-colors shadow-sm"
                      title="Open File"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Open</span>
                    </button>
                    <button
                      onClick={() => onOpenFolder(item.path)}
                      className="p-1 text-amber-600 hover:bg-amber-100 rounded"
                      title="Show Folder"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
