"
Load and process parquet (or other) files with duckdb.
"

(require hyrule [of -> ->>]) 
(import hyjinx [first group
                mkdir
                short-id now
                progress
                jsave spit])

(import duckdb)
(import json)
(import pathlib [Path])


(defclass DbError [RuntimeError])


(defn duck-load [files * [query "SELECT * FROM read_parquet('{files}')"]]
  "Load parquet files (or other SQL query) and give a generator over rows
  returned.
  Each row is returned as a dict."
  (with [con (duckdb.connect ":memory:")]
    (let [cursor (.cursor con)
          row True]
      (.execute cursor (.format query :files files))
      (let [columns (lfor desc cursor.description (first desc))]
        (while row
          (yield (setx row (dict (zip columns (.fetchone cursor)))))))
      (.close cursor))))

(defn duck-load-batch [files * [batch 1000] [query "SELECT * FROM read_parquet('{files}')"]]
  "Batch-load parquet files (or other SQL query) and
  give a generator over rows returned.
  Each row is returned as a dict."
  (with [con (duckdb.connect ":memory:")]
    (let [cursor (.cursor con)
          result True]
      (.execute cursor (.format query :files files))
      (let [columns (lfor desc cursor.description (first desc))]
        (while result
          (setx result (.fetchmany cursor batch))
          (for [row result]
            (yield (dict (zip columns row))))))
      (.close cursor))))

(defn duck-load-json [files * [query "SELECT * FROM read_json('{files}')"]]
  "Load json files (or other SQL query) and give a generator over rows
  returned.
  Each row is returned as a dict."
  (duck-load files :query query))

(defn duck-load-batch-json [files * [batch 1000] [query "SELECT * FROM read_json('{files}')"]]
  "Batch-load json files (or other SQL query) and give a generator over
  rows returned.
  Each row is returned as a dict."
  (duck-load-batch files :batch batch :query query))

  
(defn duck-save [#^ (of list dict) data #^ (| Path str) [out-dir "."] * [fmt "PARQUET"]]
  "Save a list of dicts as parquet (or other format via DuckDB).
  Inputs are not sanitized."
  (assert (in fmt #{"PARQUET" "CSV" "JSON" "NDJSON"}) "Unsupported format")
  (with [con (duckdb.connect ":memory:")]
    (.register con "data" data)
    (.execute con (.format "EXPORT data TO '{0}' (FORMAT {1})" (Path out-dir) fmt))))

(defn chunk-parquet [files field * [rows 150]] 
  "Load a set of parquet files and yield in groups of `rows`."
  (for [batch (group (duck-load-batch files) rows)]
    (yield (lfor row batch
             :if row
             (get row field)))))


;; apply template over parquet?

(defn spit-from-parquet [files #^ (| Path str) out-dir field * [rows 150]]
  "Load a set of parquet files, save (:field row) from them, as
  json chunks of `N` rows under `out-dir`."
  (let [total 0
        failed 0
        log (Path out-dir "spit-from-parquet.log")]
    (mkdir out-dir)
    (print "\n\n\n\n\n")
    (for [[n batch] (enumerate (chunk-parquet files field :rows rows))]
      (try
        (+= total (len batch))
        (let [text (.join "\n" batch)
              j {"id" (short-id text 8)
                 "added" (now)
                 "extract" text}]
          ;; fixme use tqdm
          (progress
            (.join "\n"
              ["id: {id}"
               "tokens: {tokens}"
               "total rows: {total}"
               "total batches {n}"
               "failed: {failed}"])
            :id (:id j)
            :n n
            :tokens (:length j)
            :total total
            :failed failed)
          (jsave j (Path out-dir (+ (:id j) ".json"))))
        (except [e [RuntimeError KeyError]]
          (+= failed 1)
          (spit log f"{(now)} batch {n} raised exception {(repr e)}\n" :mode "a"))))))
