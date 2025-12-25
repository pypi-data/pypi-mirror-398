#include "third_party/safari/sdk/safari/logging/cc/mcap_file_handle_factory.h"

#include <cstdint>
#include <memory>
#include <string>

#include "third_party/absl/status/statusor.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_file_handle.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_write_op.h"

namespace safari::logging {

absl::StatusOr<std::unique_ptr<BaseMcapFileHandle>>
McapFileHandleFactory::Create(const std::string& filename_prefix,
                              int64_t shard_index,
                              int64_t first_publish_time_ns,
                              const McapFileConfig* config) {
  return McapFileHandle::Create(filename_prefix, shard_index,
                                first_publish_time_ns, config);
}

}  // namespace safari::logging
