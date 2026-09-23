import assert from 'node:assert/strict';
import test from 'node:test';
import render from '../assets/ritual.js';

// Unit-test the renderer's event/timer contract without launching a browser.
function node() {
  const classes = new Set();
  return {textContent:'', innerHTML:'', disabled:false, dataset:{},
    classList:{add:c=>classes.add(c), remove:c=>classes.delete(c), toggle:(c,v)=>v?classes.add(c):classes.delete(c)},
    querySelector:()=>null};
}
function fixture() {
  const selectors = ['.coins','.toss','.result-title','.result-detail','.reveal','.count','.ladder'];
  const nodes = Object.fromEntries(selectors.map(s=>[s,node()]));
  const label = node(); nodes['.toss'].querySelector = ()=>label;
  const root = node(); root.querySelector = s=>nodes[s];
  return {nodes,label,root,parentElement:{querySelector:()=>root}};
}

test('casting renderer disables duplicate clicks and cancels stale retry timers', () => {
  const f = fixture(); const pending = new Map(); let id=0; const events=[];
  const original = {window:globalThis.window,setTimeout:globalThis.setTimeout,clearTimeout:globalThis.clearTimeout};
  globalThis.window = {matchMedia:()=>({matches:false})};
  globalThis.setTimeout = fn=>{pending.set(++id,fn);return id;};
  globalThis.clearTimeout = key=>pending.delete(key);
  try {
    render({parentElement:f.parentElement,data:{run_id:'a',lines:[],coins:null,simple:false},setTriggerValue:(key,event)=>events.push(event)});
    f.nodes['.toss'].onclick(); f.nodes['.toss'].onclick();
    assert.deepEqual(events,[{run_id:'a',index:1}]);
    assert.equal(pending.size,1);
    const retryId=id;
    render({parentElement:f.parentElement,data:{run_id:'a',lines:[7],coins:[2,2,3],simple:false},setTriggerValue:(key,event)=>events.push(event)});
    assert.equal(pending.has(retryId),false);
    assert.equal(f.nodes['.toss'].disabled,true);
    pending.get(id)(); pending.delete(id);
    assert.equal(f.label.textContent,'第 2 次投掷');
    assert.match(f.nodes['.result-detail'].textContent,/2 \+ 2 \+ 3 = 7/);
    f.nodes['.toss'].onclick();
    assert.equal(events[1].index,2);
    render({parentElement:f.parentElement,data:{run_id:'a',lines:[7,7,7,7,7,7],coins:[2,2,3],simple:true},setTriggerValue:()=>assert.fail('seventh toss')});
    assert.equal(f.nodes['.toss'].disabled,true);
    f.nodes['.toss'].onclick();
  } finally { Object.assign(globalThis,original); }
});
