<template>
  <div class="sudoku-container">
    <h1>Sudoku Solver</h1>
    <div class="sudoku-grid">
      <div v-for="(row, rowIndex) in grid" :key="rowIndex">
        <span v-for="(cell, colIndex) in row" :key="colIndex">
          <input
            type="number"
            min="1"
            max="9"
            v-model="grid[rowIndex][colIndex]"
            @focus="focusInput"
            @blur="blurInput(rowIndex, colIndex)"
            @keydown="keyDownInput($event, rowIndex, colIndex)"
            :ref="(el) => refInput(el, rowIndex, colIndex)"
            :readonly="run"
          />
        </span>
      </div>
    </div>

    <button @click="solveSudoku()">Solve</button>
    <button @click="updateSudoku()">Update</button>
    <button @click="clearSudoku()">Clear</button>

    <h3>Log:</h3>
    <textarea ref="logRef" v-model="log" readonly></textarea>
  </div>
</template>

<style scoped>
/* ----------------------------------------------
   基础 layout
---------------------------------------------- */
.sudoku-container {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
  box-sizing: border-box;
}

h1 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 2.5em;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

/* ----------------------------------------------
   Sudoku 网格
---------------------------------------------- */
.sudoku-grid {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  grid-template-rows: repeat(9, 1fr);
  border: 4px solid #34495e;
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  margin-bottom: 30px;
  background-color: #fff;
}

/* 使用 display: contents 让 span 直接遵循 9×9 布局 */
.sudoku-grid > div {
  display: contents;
}

.sudoku-grid span {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 50px;
  height: 50px;
  border: 1px solid #ccc;
  box-sizing: border-box;
}

/* ----------------------------------------------
   粗边框（3×3 宫格分界）
---------------------------------------------- */

/* 垂直粗线 */
.sudoku-grid span:nth-child(3n) {
  border-right: 2px solid #95a5a6;
}
.sudoku-grid span:nth-child(9n) {
  border-right: 4px solid #34495e;
}
.sudoku-grid span:nth-child(9n + 1) {
  border-left: 4px solid #34495e;
}

/* 水平粗线 */
.sudoku-grid > div:nth-child(3n) span {
  border-bottom: 2px solid #95a5a6;
}
.sudoku-grid > div:nth-child(9) span {
  border-bottom: 4px solid #34495e;
}
.sudoku-grid > div:nth-child(1) span {
  border-top: 4px solid #34495e;
}

/* ----------------------------------------------
   3×3 背景交错
---------------------------------------------- */

/* 默认背景 */
.sudoku-grid span {
  background-color: #e9e9e9;
}

/* 浅色背景宫 */
.sudoku-grid > div:nth-child(-n + 3) span:nth-child(-n + 3),
.sudoku-grid > div:nth-child(-n + 3) span:nth-child(n + 7),
.sudoku-grid
  > div:nth-child(n + 4):nth-child(-n + 6)
  span:nth-child(n + 4):nth-child(-n + 6),
.sudoku-grid > div:nth-child(n + 7) span:nth-child(-n + 3),
.sudoku-grid > div:nth-child(n + 7) span:nth-child(n + 7) {
  background-color: #f9f9f9;
}

/* ----------------------------------------------
   输入框
---------------------------------------------- */
input[type="number"] {
  appearance: textfield;
}

.sudoku-grid input {
  width: 100%;
  height: 100%;
  border: none;
  text-align: center;
  font-size: 1.8em;
  font-weight: bold;
  color: #333;
  background-color: transparent;
  outline: none;
  transition: background-color 0.2s ease-in-out;
}

.sudoku-grid input:focus {
  background-color: #e8f0fe !important;
}

/* ----------------------------------------------
   按钮
---------------------------------------------- */
button {
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 12px 25px;
  margin: 0 10px 20px;
  font-size: 1.1em;
  cursor: pointer;
  transition:
    background-color 0.3s ease,
    transform 0.2s ease;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

button:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
}

button:active {
  background-color: #2980b9;
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

button:nth-of-type(1) {
  background-color: #2ecc71;
}
button:nth-of-type(1):hover {
  background-color: #27ae60;
}

button:nth-of-type(2) {
  background-color: #f39c12;
}
button:nth-of-type(2):hover {
  background-color: #e67e22;
}

button:nth-of-type(3) {
  background-color: #e74c3c;
}
button:nth-of-type(3):hover {
  background-color: #c0392b;
}

/* ----------------------------------------------
   Log 区域
---------------------------------------------- */
h3 {
  color: #34495e;
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 1.5em;
}

textarea {
  width: 80%;
  max-width: 1000px;
  height: 450px;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1em;
  font-family: "Consolas", "Monaco", monospace;
  background-color: #ecf0f1;
  color: #34495e;
  resize: vertical;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
  line-height: 1.5;
}

textarea:focus {
  border-color: #3498db;
  box-shadow:
    inset 0 1px 3px rgba(0, 0, 0, 0.1),
    0 0 8px rgba(52, 152, 219, 0.5);
}
</style>

<script setup>
import { ref, nextTick, useTemplateRef } from "vue";
import { render } from "ejs";
import { Search } from "atsds";

const rule_data_url = "./Sudoku.ejs";
const logRef = useTemplateRef("logRef");
const example = `  945    
  4      
187   549
4  9  17 
 72  54 3
     4 6 
7 8   62 
92   7   
   1 2 87`;

const grid = ref(example.split("\n").map((row) => row.split("").map((cell) => parseInt(cell))));
const log = ref("");
const run = ref(false);
const inputRef = ref(Array.from({ length: 9 }, () => Array.from({ length: 9 }, () => null)));

function focusInput(event) {
    event.target.select();
}

function blurInput(rowIndex, colIndex) {
    const value = grid.value[rowIndex][colIndex];
    if (![1, 2, 3, 4, 5, 6, 7, 8, 9].includes(value)) {
        grid.value[rowIndex][colIndex] = "";
    }
}

function keyDownInput(event, row, col) {
    const { key } = event;
    let newRow = row;
    let newCol = col;
    switch (key) {
        case "ArrowUp":
            newRow = Math.max(0, row - 1);
            break;
        case "ArrowDown":
            newRow = Math.min(8, row + 1);
            break;
        case "ArrowLeft":
            newCol = Math.max(0, col - 1);
            break;
        case "ArrowRight":
            newCol = Math.min(8, col + 1);
            break;
        default:
            return;
    }
    event.preventDefault();
    const nextInput = inputRef.value[newRow][newCol];
    if (nextInput) {
        nextInput.focus();
    }
}

function refInput(el, row, col) {
    inputRef.value[row][col] = el;
}

let generator = null;

function clearSudoku() {
    grid.value = Array.from({ length: 9 }, () => Array.from({ length: 9 }, () => ""));
    log.value = "";
    run.value = false;
    generator = null;
}

async function solveSudoku() {
    if (!generator) {
        generator = search();
    }

    while (true) {
        const { value, done } = await generator.next();
        if (value) {
            addLog(`New rules/facts count: ${value}`);
        }
        if (done) {
            addLog("Sudoku solved.");
            break;
        }
        addLog("A cycle of search completed.");
        await new Promise((resolve) => setTimeout(resolve, 1));
    }
}

async function updateSudoku() {
    if (!generator) {
        generator = search();
    }

    const { value, done } = await generator.next();
    if (value) {
        addLog(`New rules/facts count: ${value}`);
    }
    if (done) {
        addLog("Search completed.");
    } else {
        addLog("Search not completed...");
    }
}

async function* search() {
    addLog("Loading Sudoku grid...");
    run.value = true;
    const response = await fetch(rule_data_url);
    const text = render(await response.text());
    const sections = text.split(/\n\n/);
    const data = sections.filter((section) => section.trim().length > 0).map((section) => section.trim());
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            const value = grid.value[row][col];
            if ([1, 2, 3, 4, 5, 6, 7, 8, 9].includes(value)) {
                addLog(`Cell (${row + 1}, ${col + 1}) = ${value}`);
                data.push(`((Cell ${row + 1} ${col + 1}) = (Literal ${value}))`);
            }
        }
    }
    addLog("Search start...");
    yield* engine(data, 1000, (candidate) => {
        if (candidate.length() === 0) {
            const text = candidate.toString();
            const match = text.match(/\(\(Cell (\d) (\d)\) = \(Literal (\d)\)\)/);
            if (match) {
                const row = parseInt(match[1]);
                const col = parseInt(match[2]);
                const value = parseInt(match[3]);
                addLog(`Cell (${row}, ${col}) = ${value}`);
                grid.value[row - 1][col - 1] = value;
            }
        }
    });
}

function addLog(message) {
    log.value += `${Date()} : ${message}\n`;
    nextTick(() => {
        logRef.value.scrollTop = logRef.value.scrollHeight;
    });
}

function* engine(input_strings, buffer_limit, callback) {
    const search = new Search(buffer_limit, buffer_limit);

    for (const input_string of input_strings) {
        search.add(input_string);
    }

    while (true) {
        const count = search.execute((rule) => {
            callback(rule);
            return false;
        });
        if (count === 0) {
            return;
        }
        yield count;
    }
}
</script>
