#ifndef THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_THREAD_POOL_LOG_WRITER_H_
#define THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_THREAD_POOL_LOG_WRITER_H_

#include <cstdint>
#include <memory>
#include <queue>
#include <string>
#include <thread>  // NOLINT
#include <utility>
#include <vector>

#include "third_party/absl/base/thread_annotations.h"
#include "third_party/absl/container/flat_hash_map.h"
#include "third_party/absl/container/flat_hash_set.h"
#include "third_party/absl/functional/any_invocable.h"
#include "third_party/absl/status/status.h"
#include "third_party/absl/status/statusor.h"
#include "third_party/absl/synchronization/mutex.h"
#include "third_party/safari/sdk/safari/logging/cc/base_mcap_file_handle_factory.h"
#include "third_party/safari/sdk/safari/logging/cc/episode_data.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_file_handle.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_write_op.h"
#include "third_party/safari/sdk/safari/protos/logging/metadata.proto.h"

namespace safari::logging {

// The default maximum number of workers to use for logging.
constexpr int64_t kDefaultMaxNumWorkers = 3;

// Configuration for creating a ThreadPoolLogWriter.
struct ThreadPoolLogWriterConfig {
  // The maximum number of threads to use for logging.
  int64_t max_num_workers = kDefaultMaxNumWorkers;
  // The keys of the image observations.
  std::vector<std::string> image_observation_keys;
  // The configuration for creating an MCAP file.
  // This is used to create an mcap file and an McapFileHandle.
  McapFileConfig mcap_file_config;
};

// Struct containing MCAP specific information for enqueuing data.
// This is passed along to the EnqueueEpisodeData and
// EnqueueSessionData methods.
struct EnqueueMcapFileOptions {
  EnqueueMcapFileOptions() = delete;
  // Constructor which can be used for enqueuing both episode and session data.
  EnqueueMcapFileOptions(std::string episode_uuid, std::string topic,
                         int64_t timestamp_ns)
      : episode_uuid(std::move(episode_uuid)),
        topic(std::move(topic)),
        timestamp_ns(timestamp_ns) {}
  // The episode UUID of the episode.
  std::string episode_uuid;
  // The topic of the MCAP channel that the data will be written to.
  std::string topic;
  // When passing session data to the EnqueueSessionData method, this field
  // represents the timestamp of the episode stop time in nanoseconds.
  int64_t timestamp_ns = 0;
};

// Class that processes and serializes data in background threads.
// After the data has been serialized to tensorflow.Example and Session protos,
// it is written to disk to an MCAP file.
// This class is thread-compatible.
// Calls to EnqueueEpisodeData() and EnqueueSessionData() are thread-safe.
// However, calls to lifecycle methods, i.e. Start() and Stop(), should not be
// called concurrently.
class ThreadPoolLogWriter {
 public:
  static absl::StatusOr<std::unique_ptr<ThreadPoolLogWriter>> Create(
      ThreadPoolLogWriterConfig config);

  ~ThreadPoolLogWriter();

  // Starts the worker threads.
  // This method is not thread-safe.
  void Start() ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Stops the worker threads. After this is called, the queue will be drained
  // and the worker threads will exit.
  // This method is not thread-safe.
  void Stop() ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Enqueues EpisodeData onto the internal queue.
  // This method is thread-safe.
  void EnqueueEpisodeData(std::unique_ptr<EpisodeData> episode_data,
                          EnqueueMcapFileOptions options)
      ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Enqueues a Session proto onto the internal queue.
  // This method is thread-safe.
  void EnqueueSessionData(safari::protos::logging::Session session,
                          EnqueueMcapFileOptions options)
      ABSL_LOCKS_EXCLUDED(queue_mutex_);

 private:
  ThreadPoolLogWriter(
      ThreadPoolLogWriterConfig config,
      std::unique_ptr<BaseMcapFileHandleFactory> mcap_file_handle_factory);

  // The main loop for the background worker threads.
  void WorkerLoop() ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Enqueues a work unit onto the internal queue.
  void Enqueue(absl::AnyInvocable<void() &&> work_unit)
      ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Work unit executed by threads to process EpisodeData.
  // Serializes each timestep of the EpisodeData into a tensorflow.Example
  // proto and calls ProcessMcapWriteOp to write the data to disk.
  void ProcessEpisodeData(std::unique_ptr<EpisodeData> episode_data,
                          EnqueueMcapFileOptions options);

  // Work unit executed by threads to process Session protos.
  // Calls ProcessMcapWriteOp to write the data to disk.
  void ProcessSessionData(safari::protos::logging::Session session,
                          EnqueueMcapFileOptions options);

  // Processes completed EpisodeData.
  // Once this method is called, ~EpisodeData will be called for each completed
  // object in the queue.
  // This method is required so that we can correctly destroy Python objects
  // encapsulated by the EpisodeData while holding onto the GIL.
  void ProcessEpisodeDataToBeDestroyed()
      ABSL_LOCKS_EXCLUDED(episode_data_to_be_destroyed_mutex_);

  // Processes a single McapWriteOp.
  absl::Status ProcessMcapWriteOp(const McapWriteOp& request)
      ABSL_LOCKS_EXCLUDED(file_handles_mutex_);

  // Returns the file handle for the given request.
  // If the file handle does not exist, or if the current file has reached
  // its size limit (set by config_->file_shard_size_limit_bytes), then a new
  // file handle is created.
  absl::StatusOr<BaseMcapFileHandle*> GetOrCreateFileHandle(
      const McapWriteOp& request)
      ABSL_EXCLUSIVE_LOCKS_REQUIRED(file_handles_mutex_);

  // Friend class for testing.
  friend class ThreadPoolLogWriterTestPeer;

  // The maximum number of workers in the thread pool. Configured in the
  // ThreadPoolLogWriterConfig.
  int64_t max_num_workers_;
  // The worker threads that process work units from the queue.
  std::vector<std::thread> workers_;

  // Mutex to protect access to the queue and the stop_ flag.
  absl::Mutex queue_mutex_;
  // Queue for storing work units.
  std::queue<absl::AnyInvocable<void() &&>> queue_
      ABSL_GUARDED_BY(queue_mutex_);
  // Flag to indicate that the pool has been stopped.
  bool stop_ ABSL_GUARDED_BY(queue_mutex_) = false;

  // Mutex to protect access to the episode_data_to_be_destroyed_ queue.
  absl::Mutex episode_data_to_be_destroyed_mutex_;
  // Queue for storing completed episode data.
  // This is used to destroy Python objects encapsulated by the EpisodeData
  // while holding onto the GIL.
  std::queue<std::unique_ptr<EpisodeData>> episode_data_to_be_destroyed_
      ABSL_GUARDED_BY(episode_data_to_be_destroyed_mutex_);

  // Values are set in the ThreadPoolLogWriter constructor
  // and are not modified afterwards. Used by worker threads during
  // serialization, but and does not require locking.
  absl::flat_hash_set<std::string> image_observation_keys_;

  // Mutex to protect access to the MCAP file handles map.
  absl::Mutex file_handles_mutex_;
  // Map of filename_prefix to McapFileHandle.
  // This is used to store McapFileHandles for each MCAP file that is being
  // written to.
  // The key is the filename_prefix, which is in the format:
  // episode_<episode_uuid> (without the shard number and .mcap extension)
  absl::flat_hash_map<std::string, std::unique_ptr<BaseMcapFileHandle>>
      file_handles_ ABSL_GUARDED_BY(file_handles_mutex_);

  // The configuration for creating an MCAP file.
  // This is used to create McapFileHandle objects and should not be modified
  // after construction.
  McapFileConfig mcap_file_config_;

  // The factory for creating McapFileHandle objects.
  std::unique_ptr<BaseMcapFileHandleFactory> mcap_file_handle_factory_;
};

}  // namespace safari::logging
#endif  // THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_THREAD_POOL_LOG_WRITER_H_
