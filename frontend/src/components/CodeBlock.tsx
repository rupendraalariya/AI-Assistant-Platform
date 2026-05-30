import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { Check, Copy } from 'lucide-react'
import toast from 'react-hot-toast'

// GitHub-dark inspired theme matching the requested code colors
const codeTheme: { [key: string]: React.CSSProperties } = {
  'code[class*="language-"]': {
    color: '#E6EDF3',
    fontFamily: '"JetBrains Mono", monospace',
    fontSize: '0.875rem',
    lineHeight: '1.6',
    background: 'none',
  },
  'pre[class*="language-"]': {
    color: '#E6EDF3',
    fontFamily: '"JetBrains Mono", monospace',
    background: '#0D1117',
    margin: 0,
    padding: '1rem',
    overflow: 'auto',
  },
  comment: { color: '#8B949E', fontStyle: 'italic' },
  prolog: { color: '#8B949E' },
  doctype: { color: '#8B949E' },
  cdata: { color: '#8B949E' },
  punctuation: { color: '#E6EDF3' },
  property: { color: '#79C0FF' },
  tag: { color: '#7EE787' },
  boolean: { color: '#79C0FF' },
  number: { color: '#79C0FF' },
  constant: { color: '#79C0FF' },
  symbol: { color: '#79C0FF' },
  selector: { color: '#7EE787' },
  'attr-name': { color: '#D2A8FF' },
  string: { color: '#A5D6FF' },
  char: { color: '#A5D6FF' },
  builtin: { color: '#FFA657' },
  inserted: { color: '#7EE787' },
  operator: { color: '#FF7B72' },
  entity: { color: '#FFA657' },
  url: { color: '#A5D6FF' },
  variable: { color: '#FFA657' },
  atrule: { color: '#D2A8FF' },
  'attr-value': { color: '#A5D6FF' },
  function: { color: '#D2A8FF' },
  'class-name': { color: '#FFA657' },
  keyword: { color: '#FF7B72' },
  regex: { color: '#A5D6FF' },
  important: { color: '#FF7B72', fontWeight: 'bold' },
}

const LANGUAGE_LABELS: Record<string, string> = {
  js: 'JavaScript',
  jsx: 'JavaScript',
  javascript: 'JavaScript',
  ts: 'TypeScript',
  tsx: 'TypeScript',
  typescript: 'TypeScript',
  py: 'Python',
  python: 'Python',
  bash: 'Bash',
  sh: 'Bash',
  shell: 'Bash',
  json: 'JSON',
  html: 'HTML',
  css: 'CSS',
  sql: 'SQL',
  go: 'Go',
  rust: 'Rust',
  java: 'Java',
  cpp: 'C++',
  c: 'C',
  yaml: 'YAML',
  markdown: 'Markdown',
}

interface CodeBlockProps {
  language: string
  value: string
}

export default function CodeBlock({ language, value }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const label = LANGUAGE_LABELS[language?.toLowerCase()] || (language ? language.toUpperCase() : 'Code')

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    toast.success('Code copied successfully')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-4 rounded-lg overflow-hidden border border-code-border bg-code-bg">
      {/* Top bar with language badge + copy button */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#161B22] border-b border-code-border">
        <span className="text-xs font-medium text-[#8B949E] font-mono">{label}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-accent" />
              <span className="text-accent">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code with syntax highlighting + line numbers */}
      <SyntaxHighlighter
        language={language || 'text'}
        style={codeTheme}
        showLineNumbers
        lineNumberStyle={{
          color: '#484F58',
          paddingRight: '1rem',
          userSelect: 'none',
          minWidth: '2.5rem',
        }}
        customStyle={{
          margin: 0,
          background: '#0D1117',
          fontSize: '0.875rem',
        }}
        wrapLongLines={false}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  )
}
