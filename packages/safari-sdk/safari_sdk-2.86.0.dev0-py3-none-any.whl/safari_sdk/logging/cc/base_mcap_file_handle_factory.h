#ifndef THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_BASE_MCAP_FILE_HANDLE_FACTORY_H_
#define THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_BASE_MCAP_FILE_HANDLE_FACTORY_H_

#include <cstdint>
#include <memory>
#include <string>

#include "third_party/absl/status/statusor.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_file_handle.h"
#include "third_party/safari/sdk/safari/logging/cc/mcap_write_op.h"

namespace safari::logging {

// Base class for creating McapFileHandle objects.
// This class is used to create McapFileHandle objects and is used to allow
// for mocking of the McapFileHandle creation in tests.
class BaseMcapFileHandleFactory {
 public:
  virtual ~BaseMcapFileHandleFactory() = default;

  virtual absl::StatusOr<std::unique_ptr<BaseMcapFileHandle>> Create(
      const std::string& filename_prefix, int64_t shard_index,
      int64_t first_publish_time_ns, const McapFileConfig* config) = 0;
};

}  // namespace safari::logging

#endif  // THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_BASE_MCAP_FILE_HANDLE_FACTORY_H_
