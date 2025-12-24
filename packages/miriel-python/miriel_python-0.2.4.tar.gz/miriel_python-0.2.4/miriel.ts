import fetch, { Headers } from 'node-fetch';
import * as fs from 'fs';
import * as path from 'path';
import * as FormData from 'form-data';

interface LearnPayload {
  user_id?: string;
  metadata?: any;
  force_string?: boolean;
  discoverable: boolean;
  grant_ids: string[];
  domain_restrictions?: any;
  recursion_depth: number;
  priority: number;
  project?: any;
  input?: string;
  chunk_size?: number;
  polling_interval?: number;
}

interface QueryPayload {
  query: string;
  user_id?: string;
  input_images?: any;
  response_format?: any;
  metadata_query?: any;
  num_results?: number;
  want_llm: boolean;
  want_vector: boolean;
  want_graph: boolean;
  mock_response?: any;
}

interface MirielOptions {
  apiKey: string;
  baseUrl?: string;
  verify?: boolean;
}

export class Miriel {
  private apiKey: string;
  private baseUrl: string;
  private verify: boolean;

  constructor({ apiKey, baseUrl = "https://api.prod.miriel.ai", verify = true }: MirielOptions) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.verify = verify;
  }

  private async makePostRequest(url: string, payload?: any, files?: any): Promise<any> {
    let headers: any = {
      'x-access-token': this.apiKey,
    };

    let response;
    if (files) {
      // For file uploads, we use FormData
      const form = new FormData();
      // append payload fields if provided
      if (payload) {
        for (const key in payload) {
          if (payload.hasOwnProperty(key)) {
            const value = payload[key];
            // Convert nested objects/arrays to JSON strings like Python does
            if (typeof value === 'object' && value !== null) {
              form.append(key, JSON.stringify(value));
            } else {
              form.append(key, value);
            }
          }
        }
      }
      // append files; expecting files to be an array of tuples
      for (const fileTuple of files) {
        const [fieldName, filename, fileStream, mimeType] = fileTuple;
        form.append(fieldName, fileStream, {
          filename: filename,
          contentType: mimeType || 'application/octet-stream'
        });
      }
      // Let form-data set its own headers
      headers = { ...headers, ...form.getHeaders(), 'Accept': 'application/json' };

      response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: form,
      });
    } else {
      // JSON request
      headers['Content-Type'] = 'application/json';
      response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload),
      });
    }

    if (response.status === 401) {
      throw new Error("Invalid API key. Please visit https://miriel.ai to sign up.");
    }
    
    if (response.status === 200 || response.status === 201) {
      try {
        return await response.json();
      } catch (err) {
        console.error("Error parsing JSON response", err);
        return null;
      }
    } else {
      console.error(`Error ${response.status}: ${await response.text()}`);
      return null;
    }
  }

  async query(query: string, user_id?: string, input_images?: any, response_format?: any, metadata_query?: any, want_llm = true, want_vector = true, want_graph = true): Promise<any> {
    const queryUrl = `${this.baseUrl}/api/v2/query`;
    const payload: QueryPayload = {
      query,
      user_id,
      input_images,
      response_format,
      metadata_query,
      want_llm,
      want_vector,
      want_graph,
    };
    return await this.makePostRequest(queryUrl, payload);
  }

  async learn(
    input: string,
    user_id?: string,
    metadata?: any,
    force_string = false,
    discoverable = true,
    grant_ids: string[] = ["*"],
    domain_restrictions?: any,
    recursion_depth = 0,
    priority: number | string = 100,
    project?: any,
    wait_for_complete = false,
    chunk_size?: number,
    polling_interval?: number
  ): Promise<any> {
    // Handle file/directory path resolution like Python does
    let isFile = false;
    let isDirectory = false;
    
    if (typeof input === 'string') {
      const expandedPath = input.startsWith('~') ? input.replace('~', process.env.HOME || process.env.USERPROFILE || '') : input;
      const resolvedPath = path.resolve(expandedPath);
      
      if (fs.existsSync(resolvedPath)) {
        isFile = true;
        isDirectory = fs.lstatSync(resolvedPath).isDirectory();
        input = resolvedPath;
      } else if (this.isUri(input) && !force_string) {
        isFile = false;
        isDirectory = false;
      } else if (this.looksLikePath(input) && !force_string) {
        throw new Error(
          `Input '${input}' looks like a file or path, but no file was found at: ${resolvedPath}.\n` +
          "Hint: If this was meant to be a text string, use force_string=true."
        );
      } else {
        isFile = false;
        isDirectory = false;
      }
    } else {
      if (!force_string) {
        throw new Error(
          `Unsupported input type: ${typeof input}. Provide a string path or literal string. ` +
          "Use force_string=true to override."
        );
      }
      isFile = false;
      isDirectory = false;
    }

    // convert string priorities to integers
    if (typeof priority === 'string') {
      if (priority === "norank") {
        priority = -1;
      } else if (priority === "pin") {
        priority = -2;
      }
    }

    const payload: LearnPayload = {
      user_id,
      metadata,
      force_string,
      discoverable,
      grant_ids,
      domain_restrictions,
      recursion_depth,
      priority: priority as number,
      chunk_size,
      polling_interval
    };

    if (project !== undefined) {
      payload.project = project;
    }

    let response;
    if (isFile) {
      const endpoint = `${this.baseUrl}/api/v2/learn`;
      const filesList: any[] = [];
      
      if (isDirectory) {
        // Walk through directory and add all files
        const walkDir = (dir: string) => {
          const addFiles = (currentDir: string) => {
            const items = fs.readdirSync(currentDir);
            for (const item of items) {
              const fullPath = path.join(currentDir, item);
              if (fs.lstatSync(fullPath).isDirectory()) {
                addFiles(fullPath);
              } else {
                filesList.push([
                  "files",  // send every file under the same field name
                  path.basename(fullPath),
                  fs.createReadStream(fullPath),
                  "application/octet-stream"
                ]);
              }
            }
          };
          addFiles(dir);
        };
        walkDir(input);
      } else {
        // Single file
        filesList.push([
          "files",
          path.basename(input),
          fs.createReadStream(input),
          "application/octet-stream"
        ]);
      }

      console.log(`Uploading ${filesList.length} files…`, payload);
      response = await this.makePostRequest(endpoint, payload, filesList);
    } else {
      const endpoint = `${this.baseUrl}/api/v2/learn`;
      payload.input = input;
      response = await this.makePostRequest(endpoint, payload);
    }

    if (wait_for_complete) {
      while ((await this.countNonCompletedLearningJobs()) > 0) {
        console.log("Waiting for all learning jobs to complete...");
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    return response;
  }

  async getLearningJobs(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_monitor_jobs`;
    return await this.makePostRequest(url, { job_status: "all" });
  }

  async countNonCompletedLearningJobs(): Promise<number> {
    const jobs = await this.getLearningJobs();
    if (!jobs) {
      return 0;
    }
    let pendingCount = 0;
    if (jobs.pending_jobs && Array.isArray(jobs.pending_jobs)) {
      for (const group of jobs.pending_jobs) {
        pendingCount += (group.job_list && Array.isArray(group.job_list)) ? group.job_list.length : 0;
      }
    }
    const queuedCount = jobs.queued_items && Array.isArray(jobs.queued_items) ? jobs.queued_items.length : 0;
    return pendingCount + queuedCount;
  }

  async updateDocument(document_id: string, user_id?: string, metadata?: any, discoverable = true, grant_ids: string[] = ["*"], chunk_size?: number): Promise<any> {
    const url = `${this.baseUrl}/api/v2/update_document`;
    const payload = { user_id, document_id, metadata, discoverable, grant_ids, chunk_size };
    return await this.makePostRequest(url, payload);
  }

  async createUser(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/create_user`;
    return await this.makePostRequest(url, {});
  }

  async setDocumentAccess(user_id: string, document_id: string, grant_ids: string[]): Promise<any> {
    const url = `${this.baseUrl}/api/v2/set_document_access`;
    const payload = { user_id, document_id, grant_ids };
    return await this.makePostRequest(url, payload);
  }

  async getDocumentById(document_id: string, user_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_document_by_id`;
    const payload = { user_id, document_id };
    return await this.makePostRequest(url, payload);
  }

  async getMonitorSources(user_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_monitor_sources`;
    return await this.makePostRequest(url, { user_id });
  }

  async removeAllDocuments(user_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/remove_all_documents`;
    return await this.makePostRequest(url, { user_id });
  }

  async getUsers(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_users`;
    return await this.makePostRequest(url, {});
  }

  async deleteUser(user_id: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/delete_user`;
    const payload = { user_id };
    return await this.makePostRequest(url, payload);
  }

  async getProjects(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_projects`;
    return await this.makePostRequest(url, {});
  }

  async createProject(name: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/create_project`;
    const payload = { name };
    return await this.makePostRequest(url, payload);
  }

  async deleteProject(project_id: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/delete_project`;
    const payload = { project_id };
    return await this.makePostRequest(url, payload);
  }

  async getDocumentCount(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_document_count`;
    return await this.makePostRequest(url, {});
  }

  async getUserPolicies(): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_user_policies`;
    return await this.makePostRequest(url, {});
  }

  async addUserPolicy(policy: any, project_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/add_user_policy`;
    const payload: any = { policy };
    if (project_id !== undefined) {
      payload.project_id = project_id;
    }
    return await this.makePostRequest(url, payload);
  }

  async deleteUserPolicy(policy_id: string, project_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/delete_user_policy`;
    const payload: any = { policy_id };
    if (project_id !== undefined) {
      payload.project_id = project_id;
    }
    return await this.makePostRequest(url, payload);
  }

  async removeDocument(document_id: string, user_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/remove_document`;
    const payload = { document_id, user_id };
    return await this.makePostRequest(url, payload);
  }

  async getAllDocuments(user_id?: string, project?: any, metadata_query?: any): Promise<any> {
    const url = `${this.baseUrl}/api/v2/get_all_documents`;
    const payload: any = {};
    if (user_id !== undefined) {
      payload.user_id = user_id;
    }
    if (project !== undefined) {
      payload.project = project;
    }
    if (metadata_query !== undefined) {
      payload.metadata_query = metadata_query;
    }
    return await this.makePostRequest(url, payload);
  }

  async removeResource(resource_id: string, user_id?: string): Promise<any> {
    const url = `${this.baseUrl}/api/v2/remove_resource`;
    const payload: any = { resource_id };
    if (user_id !== undefined) {
      payload.user_id = user_id;
    }
    return await this.makePostRequest(url, payload);
  }

  private looksLikePath(s: string): boolean {
    s = s.trim();
    const commonFileExtensions = [
      // Documents
      '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.tex', '.md', '.markdown',
      // Spreadsheets / Data
      '.csv', '.tsv', '.xls', '.xlsx', '.ods', '.json', '.xml', '.yaml', '.yml', '.parquet',
      // Presentations
      '.ppt', '.pptx', '.odp',
      // Code / Config
      '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.rb', '.go', '.sh', '.html', '.css',
      '.ipynb', '.ini', '.cfg', '.env', '.toml', '.bat',
      // Images
      '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff', '.webp', '.ico',
      // Archives / Compressed
      '.zip', '.tar', '.gz', '.rar', '.7z', '.xz',
      // Audio / Video
      '.mp3', '.wav', '.aac', '.flac', '.ogg',
      '.mp4', '.mov', '.avi', '.mkv', '.webm',
      // Misc
      '.log', '.db', '.sqlite', '.bin', '.exe'
    ];
    
    return (
      s.startsWith("~") || s.startsWith(".") || s.startsWith("..") || s.startsWith(path.sep) ||
      (process.platform === "win32" && /^[a-zA-Z]:[\\/]/.test(s)) ||
      s.includes(path.sep) ||
      commonFileExtensions.some(ext => s.toLowerCase().endsWith(ext))
    );
  }

  private isUri(s: string): boolean {
    try {
      const url = new URL(s);
      const supportedSchemes = [
        'http', 'https', 'file', 'folder', 'directory', 'dir',
        's3', 'rtsp', 'discord', 'gcalendar', 'string'
      ];
      return supportedSchemes.includes(url.protocol.replace(':', ''));
    } catch {
      return false;
    }
  }
}