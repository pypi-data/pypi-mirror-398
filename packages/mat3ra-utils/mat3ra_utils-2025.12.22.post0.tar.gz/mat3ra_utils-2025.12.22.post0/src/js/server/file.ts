import * as fs from "fs";
import { access, mkdir, readdir, rm } from "node:fs/promises";
import path from "node:path";

type FileExtension = "in" | "sh" | "bash" | "zsh" | "pbs" | "py";

const FILE_EXTENSION_TO_PROGRAMMING_LANGUAGE_MAP: { [key in FileExtension]: string } = {
    in: "fortran",
    sh: "shell",
    bash: "shell",
    zsh: "shell",
    pbs: "shell",
    py: "python",
};

/**
 * @summary Identifies language by file extension. Uses 'fortran' by default.
 */
export function getProgrammingLanguageFromFileExtension(
    filename: string,
    defaultLanguage = "fortran",
) {
    const fileExt = filename.split(".").pop()?.toLowerCase();
    if (!fileExt) {
        return defaultLanguage;
    }
    return FILE_EXTENSION_TO_PROGRAMMING_LANGUAGE_MAP[fileExt as FileExtension] || defaultLanguage;
}

/**
 * @summary Formats a given file size.
 * @param size file size.
 * @param decimals number of decimals to round.
 */
export function formatFileSize(size: number, decimals = 2) {
    if (size === 0) return "0 Bytes";
    const index = Math.floor(Math.log(size) / Math.log(1024));
    const units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    return parseFloat((size / 1024 ** index).toFixed(decimals)) + " " + units[index];
}

/** Get list of paths for files in a directory and filter by file extensions if provided.
 * @param dirPath - Path to current directory, i.e. $PWD
 * @param fileExtensions - File extensions to filter, e.g. `.yml`
 * @param resolvePath - whether to resolve the paths of files
 * @returns - Array of file paths
 */
export function getFilesInDirectory(
    dirPath: string,
    fileExtensions: string[] = [],
    resolvePath = true,
) {
    let fileNames = fs.readdirSync(dirPath);
    if (fileExtensions.length) {
        fileNames = fileNames.filter((dirItem) => fileExtensions.includes(path.extname(dirItem)));
    }
    if (resolvePath) return fileNames.map((fileName) => path.resolve(dirPath, fileName));
    return fileNames;
}

/**
 * Get list of directories contained in current directory.
 * @param currentPath - current directory
 */
export function getDirectories(currentPath: string) {
    return fs
        .readdirSync(currentPath, { withFileTypes: true })
        .filter((dirent) => dirent.isDirectory())
        .map((dirent) => dirent.name);
}

/**
 * Construct object path compatible with lodash.get/lodash.set from file path.
 * Note: if no root path is provided the file's dirname is taken instead.
 * @param filePath - Path to file.
 * @param root - Path to a parent directory to construct relative path.
 * @return - Object path reflecting file path.
 * @example
 * createObjectPathFromFilePath("/a/b/c/d/e.yml", "/a/b");
 * // "['c']['d']['e']"
 */
export function createObjectPathFromFilePath(filePath: string, root: string) {
    const dirname = path.dirname(filePath);
    const extension = path.extname(filePath);
    const basename = path.basename(filePath, extension);
    const parentDirs = root ? path.relative(root, dirname).split(path.sep) : [];
    return [...parentDirs, basename].map((item) => `['${item}']`).join("");
}

export async function createDirIfNotExists(directory: string) {
    try {
        await access(directory);
    } catch (err) {
        await mkdir(directory, { recursive: true });
    }
}

export function createDirIfNotExistsSync(directoryPath: string) {
    if (!fs.existsSync(directoryPath)) {
        fs.mkdirSync(directoryPath, { recursive: true });
    }
}

export async function cleanDirectory(directory: string) {
    const files = await readdir(directory, { withFileTypes: true });

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.isDirectory()) {
            // eslint-disable-next-line no-await-in-loop
            await rm(path.join(directory, file.name), { recursive: true, force: true });
        } else {
            // eslint-disable-next-line no-await-in-loop
            await rm(path.join(directory, file.name));
        }
    }
}

/**
 * Remove all files and folders in a directory except those specified to omit.
 * @param directoryPath
 * @param omitFiles
 */
export function cleanDirectorySync(directoryPath: string, omitFiles: string[] = []) {
    if (!fs.existsSync(directoryPath)) {
        return;
    }
    const files = fs.readdirSync(directoryPath, { withFileTypes: true });

    files.forEach((file) => {
        if (omitFiles.includes(file.name)) {
            return;
        }
        const filePath = path.join(directoryPath, file.name);
        if (file.isDirectory()) {
            fs.rmSync(filePath, { recursive: true, force: true });
        } else {
            fs.unlinkSync(filePath);
        }
    });
}
