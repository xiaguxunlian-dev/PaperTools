/**
 * config.js — 配置管理 (JavaScript Port)
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.research-suite');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const DEFAULT_KEYS = [
    { name: 'pubmed',       label: 'PubMed API Key',       required: false },
    { name: 'arxiv',        label: 'arXiv',                 required: false },
    { name: 'semantic',     label: 'Semantic Scholar',      required: false },
    { name: 'openalex',     label: 'OpenAlex',              required: false },
    { name: 'crossref',     label: 'CrossRef',              required: false },
    { name: 'bgpt',         label: 'BGPT API Key',          required: false },
];

class Config {
    constructor() {
        this._ensureDir();
        this._config = this._load();
    }

    _ensureDir() {
        if (!fs.existsSync(CONFIG_DIR)) {
            try { fs.mkdirSync(CONFIG_DIR, { recursive: true }); } catch(e) {}
        }
    }

    _load() {
        if (fs.existsSync(CONFIG_FILE)) {
            try {
                return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
            } catch(e) {}
        }
        return {
            api_keys: {},
            defaults: { max_results: 20, default_dbs: ['pubmed','arxiv','semantic'], language: 'zh-CN' },
            preferences: {},
        };
    }

    _save() {
        try {
            fs.writeFileSync(CONFIG_FILE, JSON.stringify(this._config, null, 2), 'utf-8');
        } catch(e) { console.error('Config save error:', e); }
    }

    getApiKeys() { return DEFAULT_KEYS.map(k => ({ ...k, value: this._config.api_keys?.[k.name] || null })); }
    getApiKey(name) { return this._config.api_keys?.[name] || null; }

    setApiKey(name, value) {
        if (!this._config.api_keys) this._config.api_keys = {};
        this._config.api_keys[name] = value;
        this._save();
    }

    listApiKeys() { return this.getApiKeys(); }
    get(key, fallback) { return this._config[key] ?? fallback; }
    set(key, value) { this._config[key] = value; this._save(); }
}

module.exports = { Config };
