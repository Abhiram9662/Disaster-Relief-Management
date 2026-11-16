/**
 * Local-first IndexedDB offline store and queued writes manager.
 */

const DB_NAME = 'ReliefCoordinatorDB';
const DB_VERSION = 1;

class PWAStore {
  constructor() {
    this.db = null;
    this.initPromise = this.init();
  }

  init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('volunteers')) {
          db.createObjectStore('volunteers', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('needs')) {
          db.createObjectStore('needs', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('assignments')) {
          db.createObjectStore('assignments', { keyPath: 'assignment_id' });
        }
        if (!db.objectStoreNames.contains('queued_writes')) {
          db.createObjectStore('queued_writes', { autoIncrement: true, keyPath: 'queue_id' });
        }
      };

      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve(this.db);
      };

      request.onerror = (e) => {
        console.error('IndexedDB init error:', e);
        reject(e);
      };
    });
  }

  async saveItems(storeName, items) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      items.forEach(item => store.put(item));
      tx.oncomplete = () => resolve();
      tx.onerror = (e) => reject(e);
    });
  }

  async getAll(storeName) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = (e) => reject(e);
    });
  }

  async queueWrite(type, payload) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction('queued_writes', 'readwrite');
      const store = tx.objectStore('queued_writes');
      const req = store.add({
        type: type,
        payload: payload,
        timestamp: Date.now()
      });
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e);
    });
  }

  async flushQueue(apiBaseUrl = '') {
    await this.initPromise;
    const items = await this.getAll('queued_writes');
    if (!items.length) return 0;

    let flushedCount = 0;
    for (const item of items) {
      try {
        let endpoint = '';
        if (item.type === 'volunteer') endpoint = '/api/volunteers';
        else if (item.type === 'need') endpoint = '/api/needs';
        else if (item.type === 'confirm') endpoint = `/api/assignments/${item.payload.assignment_id}/confirm`;

        if (endpoint) {
          const res = await fetch(`${apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item.payload)
          });
          if (res.ok) {
            flushedCount++;
          }
        }
      } catch (err) {
        console.warn('Queue flush item deferred:', err);
        break; // Stop flushing if still offline
      }
    }

    if (flushedCount > 0) {
      // Clear processed items
      const tx = this.db.transaction('queued_writes', 'readwrite');
      tx.objectStore('queued_writes').clear();
    }
    return flushedCount;
  }
}

window.pwaStore = new PWAStore();
