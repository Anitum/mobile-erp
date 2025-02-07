import React, { useState } from 'react';
import { Eye, Maximize2, Minimize2, X } from 'lucide-react';

const AdminTaskViewer = ({ taskFile }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!taskFile) {
    return <span className="text-gray-500">No file</span>;
  }

  return (
    <div className="inline-flex">
      {/* View Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center justify-center w-8 h-8 text-gray-600 bg-gray-100 rounded-full hover:bg-gray-200"
      >
        <Eye className="w-4 h-4" />
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className={`bg-white rounded-lg ${isFullscreen ? 'fixed inset-0' : 'w-11/12 h-5/6 max-w-6xl'}`}>
            {/* Modal Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h3 className="text-lg font-semibold">Task Attachment</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 text-gray-500 hover:text-gray-700"
                >
                  {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-gray-500 hover:text-gray-700"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* File Content */}
            <div className="w-full h-full p-4">
              <iframe
                src={`/admin/task-file/${encodeURIComponent(taskFile)}`}
                className="w-full h-full border-0"
                title="Task File Viewer"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminTaskViewer;