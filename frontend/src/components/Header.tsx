/**
 * Header Component
 */

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">
              Pipeline n8n Alternative
            </h1>
          </div>
          <nav className="flex space-x-4">
            <a
              href="/"
              className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Pipelines
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
