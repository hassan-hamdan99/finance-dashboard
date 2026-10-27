import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, CheckCircle, FileUp } from 'lucide-react';
import api from '../api/client';
import { usePersons } from '../api/hooks';
import type { UploadPreview } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

const BANKS = [
  'Auto',
  'Nubank',
  'Itaú',
  'Bradesco',
  'Inter',
  'C6',
  'Santander',
  'BB',
  'Caixa',
];

export default function Upload() {
  const [person, setPerson] = useState('');
  const [bank, setBank] = useState('Auto');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState<number | null>(null);
  const [error, setError] = useState('');

  const { data: persons = [] } = usePersons();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/x-ofx': ['.ofx'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    onDrop: (accepted) => {
      if (accepted.length > 0) {
        setFile(accepted[0]);
        setPreview(null);
        setConfirmed(null);
        setError('');
      }
    },
  });

  async function handlePreview() {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (person) fd.append('person', person);
      fd.append('bank', bank);
      const res = await api.post('/api/upload/preview', fd);
      setPreview(res.data);
    } catch {
      setError('Erro ao processar arquivo');
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (person) fd.append('person', person);
      fd.append('bank', bank);
      const res = await api.post('/api/upload/confirm', fd);
      setConfirmed(res.data.imported ?? res.data.new_count ?? 0);
      setPreview(null);
      setFile(null);
    } catch {
      setError('Erro ao importar');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Config */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
          <input
            type="text"
            value={person}
            onChange={(e) => setPerson(e.target.value)}
            placeholder="Nome da pessoa"
            list="persons-list"
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
          <datalist id="persons-list">
            {persons.map((p) => (
              <option key={p} value={p} />
            ))}
          </datalist>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Banco</label>
          <select
            value={bank}
            onChange={(e) => setBank(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            {BANKS.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-indigo-500 bg-indigo-600/10'
            : 'border-[#2a2a4a] hover:border-gray-500 bg-[#1a1a2e]'
        }`}
      >
        <input {...getInputProps()} />
        <UploadIcon className="w-10 h-10 mx-auto mb-3 text-gray-500" />
        {file ? (
          <p className="text-gray-200">
            <FileUp className="inline w-4 h-4 mr-1" />
            {file.name}
          </p>
        ) : isDragActive ? (
          <p className="text-indigo-400">Solte o arquivo aqui</p>
        ) : (
          <p className="text-gray-400">
            Arraste um arquivo <strong>.ofx</strong> ou <strong>.csv</strong>{' '}
            aqui, ou clique para selecionar
          </p>
        )}
      </div>

      {/* Preview button */}
      {file && !preview && (
        <button
          onClick={handlePreview}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-6 py-2 disabled:opacity-50"
        >
          {loading ? 'Processando...' : 'Pré-visualizar'}
        </button>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Success */}
      {confirmed !== null && (
        <div className="bg-green-600/15 border border-green-600/30 rounded-xl p-5 flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-400" />
          <p className="text-green-300">
            {confirmed} transações importadas com sucesso!
          </p>
        </div>
      )}

      {/* Preview table */}
      {preview && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              <span className="text-green-400 font-medium">
                {preview.new_count} novas
              </span>{' '}
              &middot;{' '}
              <span className="text-yellow-400 font-medium">
                {preview.dup_count} duplicadas
              </span>{' '}
              &middot; Banco: {preview.bank}
            </div>
            <button
              onClick={handleConfirm}
              disabled={loading || preview.new_count === 0}
              className="bg-green-600 hover:bg-green-500 text-white rounded-lg px-5 py-2 disabled:opacity-50"
            >
              {loading ? 'Importando...' : `Confirmar (${preview.new_count})`}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                  <th className="py-2 px-2">Data</th>
                  <th className="py-2 px-2">Descrição</th>
                  <th className="py-2 px-2 text-right">Valor</th>
                  <th className="py-2 px-2">Categoria</th>
                  <th className="py-2 px-2">Fornecedor</th>
                  <th className="py-2 px-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {preview.transactions.map((t, i) => (
                  <tr
                    key={i}
                    className={`border-b border-[#2a2a4a] ${
                      t.is_duplicate ? 'opacity-40' : ''
                    }`}
                  >
                    <td className="py-2 px-2 text-gray-300">{t.date}</td>
                    <td className="py-2 px-2 text-gray-200 max-w-xs truncate">
                      {t.description}
                    </td>
                    <td
                      className={`py-2 px-2 text-right font-medium ${
                        t.amount < 0 ? 'text-red-400' : 'text-green-400'
                      }`}
                    >
                      {fmt.format(t.amount)}
                    </td>
                    <td className="py-2 px-2 text-gray-300">
                      {t.category_name ?? '-'}
                    </td>
                    <td className="py-2 px-2 text-gray-300">
                      {t.vendor ?? '-'}
                    </td>
                    <td className="py-2 px-2">
                      {t.is_duplicate ? (
                        <span className="text-yellow-400 text-xs">Duplicada</span>
                      ) : (
                        <span className="text-green-400 text-xs">Nova</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
